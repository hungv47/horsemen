import unittest
from copy import deepcopy
from brain import Brain, Patch, BrainError
from drive_adapter import DocsProvider

class Tests(unittest.TestCase):
    def setUp(self):
        self.raw={'documentId':'one','revisionId':'r1','body':{'content':[{'startIndex':1,'endIndex':9,'paragraph':{'elements':[{'startIndex':1,'endIndex':9,'textRun':{'content':'Hi old!\n'}}]}}]}}
        self.calls=[]
        self.p=DocsProvider(lambda key:deepcopy(self.raw),lambda **kw:self.calls.append(kw),lambda q:['one'])
    def test_read(self): self.assertEqual(self.p.read('one').text,'Hi old!\n')
    def test_guard_and_precise_native_range(self):
        self.p.replace('one','r1','Hi old!\n','Hi new!\n')
        self.assertEqual(self.calls[0]['write_control'],{'requiredRevisionId':'r1'})
        self.assertEqual(self.calls[0]['requests'],[{'deleteContentRange':{'range':{'startIndex':4,'endIndex':7}}},{'insertText':{'location':{'index':4},'text':'new'}}])
    def test_conflict(self):
        with self.assertRaises(BrainError): self.p.replace('one','stale','Hi old!\n','Hi new!\n')
        self.assertEqual(self.calls,[])
    def test_no_revision(self):
        del self.raw['revisionId']
        with self.assertRaises(BrainError): self.p.read('one')
    def test_table_rejected(self):
        self.raw['body']['content'].append({'table':{}})
        with self.assertRaises(BrainError): self.p.read('one')
    def test_suggestion_rejected(self):
        self.raw['body']['content'][0]['paragraph']['elements'][0]['suggestedInsertionIds']=['x']
        with self.assertRaises(BrainError): self.p.read('one')
    def test_wrong_id(self):
        self.raw['documentId']='other'
        with self.assertRaises(BrainError): self.p.read('one')
    def test_final_newline_protected(self):
        with self.assertRaises(BrainError): self.p.replace('one','r1','Hi old!\n','Hi new!')
    def test_utf16_offsets(self):
        self.raw['body']['content']=[{'paragraph':{'elements':[{'startIndex':1,'endIndex':10,'textRun':{'content':'😀 old!!\n'}}]}}]
        self.p.replace('one','r1','😀 old!!\n','😀 new!!\n')
        self.assertEqual(self.calls[0]['requests'][0]['deleteContentRange']['range'],{'startIndex':4,'endIndex':7})
    def test_tabs_rejected(self):
        self.raw['tabs']=[{'documentTab':{}},{'documentTab':{}}]
        with self.assertRaises(BrainError): self.p.read('one')
    def test_append_preserves_terminator(self):
        self.p.replace('one','r1','Hi old!\n','Hi old!\nNext\n')
        self.assertEqual(self.calls[0]['requests'],[{'insertText':{'location':{'index':8},'text':'\nNext'}}])
    def test_paragraph_suggestion_rejected(self):
        self.raw['body']['content'][0]['paragraph']['suggestedParagraphStyleChanges']={'x':{}}
        with self.assertRaises(BrainError): self.p.read('one')
    def test_no_change_no_batch(self):
        self.p.replace('one','r1','Hi old!\n','Hi old!\n'); self.assertEqual(self.calls,[])
    def test_denial_never_calls_batch(self):
        b=Brain(self.p); self.assertEqual(b.apply(b.prepare('one',Patch('old','new')),lambda p:False).status,'denied')
        self.assertEqual(self.calls,[])

if __name__=='__main__': unittest.main()
