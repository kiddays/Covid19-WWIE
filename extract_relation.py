import json
import spacy
import string

from spacy import displacy
from collections import defaultdict, deque, Counter

LABELS = {'CHEMICAL', 'DISEASE', 'GENE', 'PROTEIN'}

def create_dict(doc):
    offsets = {}
    for i, x in enumerate(doc):
        offsets[x] = i
    return offsets

def get_offset(token, offsets):
    return offsets[token]


def find_root(doc):
    for token in doc:
        if token.dep_ == 'ROOT':
            return token
    return None

def append_children(token, l):
    for c in token.children:
        l.append(c)

def make_nested_info(lists):
    '''
    make nested information as needed
    'A can reduce B'
    'B caused by C"
    -> 'A can reduce B <caused by C>'
    '''
    res = []
    for i in range(len(lists)):
        res.append(' '.join([t.text for t in lists[0]]))
        if i > 0:
            curr = [token.text for token in lists[i]]
            for token in lists[i]:
                if (token.pos_ == 'NOUN' or token.pos_ == 'PROPN') and token in lists[i - 1]:
                    prev = [token.text for token in lists[i - 1]]
                    idx_dict = {}
                    for n, tok in enumerate(prev):
                        idx_dict[tok] = n
                    prev.insert(idx_dict[tok] + 1, '<' + ' '.join(curr) + '>')
                    prev_str = ' '.join(prev)
                    if prev_str not in res:
                        res.append(prev_str)
                else:
                    curr_str = ' '.join(curr)
                    if curr_str not in res:
                        res.append(curr_str)
                    i += 1
    return res

def list_toke_to_str(l):
    return [token.text for token in l]

def get_relation(doc, nps):
    tups = []
    i = 0
    if len(nps) > 0:
        for token in doc:
            if token.pos_ == 'VERB':
                tup = tuple((token.text, list_toke_to_str(nps[i])))
                tups.append(tup)
    print(tups)
    tup_dict = defaultdict(list)

    # collapsing relations
    for tup in tups:
        tup_dict[', '.join(tup[1])].append((tup[0]))
    res = [tuple((' '.join(tup_dict[k]), k)) for k in tup_dict.keys()]
    print(res)
    return res


def bfs(doc, res):
    root = find_root(doc)
    if root == None or root.children == None:
        return res
    # level order traversal
    q = deque([root])
    while q:
        curr = []
        n = q.popleft()
        if n.children:
            for i in n.children:
                if n.pos_ == 'VERB' and (i.pos_ == 'NOUN' or i.pos_ == 'PROPN'):
                    curr.append(i)
                q.append(i)
        if len(curr) > 0:
            res.append(curr)
    print(res)
    return res


def get_propn_count(l):
    num = 0
    for token in l:
        if token.pos_ == 'PROPN':
            num += 1
    return num


def remove_sectionname(string):
    l = string.split()
    if l[1] == ':':
        return ' '.join(l[2:])
    return string


def get_chunks(doc):
    return [chunk for chunk in doc.noun_chunks]


def get_propns(doc):
    return [token for token in doc if token.pos_ == 'PROPN']


def link_entity(ent_doc, label_doc):
    # get bio entities
    ent_labels = [] # bioNER labels
    ent_tokens = [token.text for token in ent_doc] # tokens in ent_doc
    label_tokens = [token.text for token in label_doc] # tokens in label_doc

    for token in label_doc:
        for label in LABELS:
            if label in token.text:
                ent_labels.append(token)

    # get original noun chunks
    replaced_chunks = []
    chunks = get_chunks(ent_doc)
    for chunk in chunks:
        for token in chunk:
            # entity got replaced -> missing in ent_doc
            if token.text not in label_tokens:
                replaced_chunks.append(chunk)

    replaced_chunks = list(dict.fromkeys(replaced_chunks))
    
    # get token-index dict
    idx_dict = create_dict(label_doc)

    output = [token.text for token in label_doc]

    # get proper nouns from original ent_doc
    propns = get_propns(ent_doc)

    ents_counter = Counter(ent_tokens)
    labels_counter = Counter(label_tokens)

    # find proper nouns present in original doc, but missing in labeled doc
    for propn in propns:
        if propn not in labels_counter or ents_counter[propn] < labels_counter[propn]:
            replaced_chunks.append(propn)

    # combine ents with labels
    # avoid index out of range
    combined_dict = {}
    for i in range(min(len(ent_labels), len(replaced_chunks))):
        label_idx = get_offset(ent_labels[i], idx_dict)
        output[label_idx] += ' -- ' + '<' + replaced_chunks[i].text + '>'
        combined_dict[ent_labels[i]] = replaced_chunks[i].text
    
    combined = ' '.join(output)
    print(combined)
    return(combined, combined)




if __name__ == "__main__":
    nlp = spacy.load("en_core_web_sm")
    merge_nps = nlp.create_pipe("merge_noun_chunks")
    nlp.add_pipe(merge_nps)

    # sample = 'Several have confirmed GENE presence in human brains , and the GENE association in DISEASE . '
    sample = 'The DISEASE in 2009 caused 18,000 deaths 1,2 .'
    doc = nlp(remove_sectionname(sample))
    offsets = create_dict(doc)
    nps = bfs(doc, [])
    get_relation(doc, nps)
    

    l = 'The DISEASE in 2009 caused 18,000 deaths 1,2 .'
    e = 'The sudden swine-origin influenza virus H1N1v pandemic outbreak in 2009 caused 18,000 deaths 1,2 . '
    doc_l = nlp(remove_sectionname(l))
    doc_e = nlp(remove_sectionname(e))
    link_entity(doc_e, doc_l)

    # with open('./combined_data.jsonl_new', 'r') as json_file_labels:
    #     json_list_labels = list(json_file_labels)
    # json_file_labels.close()

    # with open('./original_data.jsonl_new', 'r') as json_file_ents:
    #     json_list_ents = list(json_file_ents)
    # json_file_ents.close()


    # for i, j in enumerate(json_list_labels):
    #     json_dict_labels = json.loads(json_list_labels[i])
    #     json_dict_ents = json.loads(json_list_ents[i])
    #     text_labels = remove_sectionname(json_dict_labels['text'])
    #     text_ents = remove_sectionname(json_dict_ents['text'])
    #     doc_labels = nlp(text_labels)
    #     doc_ents = nlp(text_ents)

    #     # extraction
    #     nps = bfs(doc_labels, [])
    #     print(get_relation(doc_labels, nps))
    #     # combine label and entities
    #     link_entity(doc_labels, doc_ents)
    #     print('=====')