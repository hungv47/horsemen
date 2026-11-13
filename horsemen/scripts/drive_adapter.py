"""Guarded Google Docs transport adapter; no auth, network client or mount writes.

Host supplies approved get_document, batch_update_document and scoped search
callbacks. Callbacks unwrap the native API object and raise on tool/API errors.
"""
from brain import Document, BrainError


def units(text):
    return len(text.encode('utf-16-le')) // 2


class DocsProvider:
    def __init__(self, get_document, batch_update_document, search_ids):
        self.get_document = get_document
        self.batch_update_document = batch_update_document
        self.search_ids = search_ids

    def search(self, query):
        return [self.read(key) for key in self.search_ids(query)]

    def read(self, identity):
        raw = self.get_document(identity)
        if raw.get('documentId') != identity:
            raise BrainError('original identity mismatch')
        revision = raw.get('revisionId')
        if not isinstance(revision, str) or not revision.strip():
            raise BrainError('revision unavailable; writes disabled')
        # Deliberately narrow first adapter: classic body-only documents.
        # Tabs, suggestions, objects and tables require native structural plans.
        if raw.get('tabs') or raw.get('suggestedDocumentStyleChanges'):
            raise BrainError('unsupported tabs or suggestions')
        chunks=[]
        index=1
        for item in raw.get('body', {}).get('content', []):
            if 'sectionBreak' in item and not chunks and item.get('endIndex') == 1:
                continue
            if 'paragraph' not in item:
                raise BrainError('unsupported body structure')
            if set(item['paragraph']) - {'elements', 'paragraphStyle'}:
                raise BrainError('unsupported paragraph structure or suggestion')
            for element in item['paragraph'].get('elements', []):
                if set(element) - {'startIndex','endIndex','textRun'}:
                    raise BrainError('unsupported element or suggestion')
                run = element.get('textRun', {})
                if set(run) - {'content','textStyle'}:
                    raise BrainError('unsupported text run')
                text = run.get('content')
                if not isinstance(text, str) or element.get('startIndex') != index:
                    raise BrainError('noncontiguous native range')
                index += units(text)
                if element.get('endIndex') != index:
                    raise BrainError('invalid UTF-16 native range')
                chunks.append(text)
        text = ''.join(chunks)
        if not text.endswith('\n'):
            raise BrainError('missing document terminator')
        return Document('google-docs', identity, f'https://docs.google.com/document/d/{identity}/edit', revision, text)

    def replace(self, identity, revision, before, after):
        current = self.read(identity)
        if (current.revision,current.text) != (revision,before):
            raise BrainError('conflict')
        if before == after:
            return
        if not after.endswith('\n'):
            raise BrainError('cannot remove final document newline')
        # Derive one minimal native range, preserving all surrounding structure.
        prefix=0
        while prefix < min(len(before)-1,len(after)-1) and before[prefix] == after[prefix]:
            prefix+=1
        suffix=0
        while suffix < min(len(before)-prefix,len(after)-prefix) and before[-suffix-1] == after[-suffix-1]:
            suffix+=1
        old_end=len(before)-suffix
        new_end=len(after)-suffix
        start=1+units(before[:prefix])
        end=1+units(before[:old_end])
        requests=[]
        if end>start:
            requests.append({'deleteContentRange':{'range':{'startIndex':start,'endIndex':end}}})
        if after[prefix:new_end]:
            requests.append({'insertText':{'location':{'index':start},'text':after[prefix:new_end]}})
        # requiredRevisionId fails on drift; targetRevisionId would merge and is
        # intentionally forbidden. One atomic batch, never an unguarded retry.
        self.batch_update_document(document_id=identity, requests=requests,
                                   write_control={'requiredRevisionId':revision})
