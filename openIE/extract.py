import json
import spacy
import string

from spacy import displacy
from collections import defaultdict, deque, Counter


nlp = spacy.load("en_core_web_sm")
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

def bfs(doc, lists):
    offsets = create_dict(doc)

    def get_offset(token):
        return offsets[token]

    root = find_root(doc)
    if root == None or root.children == None:
        return lists
    # level order traversal
    q = deque([root])
    while q:
        curr = []
        n = q.popleft()
        if n.children:
            curr.append(n)
            for i in n.children:
                if i.pos_ != 'PUNCT':
                    curr.append(i)
                if i.pos_ == 'ADP' or i.pos_ == 'CONJ' or i.pos_ == 'VERB':
                    if i.children:
                        append_children(i, curr)
                q.append(i)
        curr.sort(key=get_offset)
        if (len(curr) > 2):
            # lists.append(curr)
            str_curr = [x.text for x in curr]
            lists.append(' '.join(str_curr))
    return lists


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
        if token.text in LABELS:
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

    # print(ent_labels)
    # print(replaced_chunks)
    
    # get token-index dict
    idx_dict = create_dict(label_doc)

    output = [token.text for token in label_doc]

    # get proper nouns from original ent_doc
    propns = get_propns(ent_doc)

    ents_counter = Counter(ent_tokens)
    labels_counter = Counter(label_tokens)
    # print(ents_counter)
    # print(labels_counter)

    # find proper nouns present in original doc, but missing in labeled doc
    for propn in propns:
        if propn not in labels_counter or ents_counter[propn] < labels_counter[propn]:
            replaced_chunks.append(propn)
            # print(propn)

    # combine ents with labels
    # avoid index out of range
    for i in range(min(len(ent_labels), len(replaced_chunks))):
        label_idx = get_offset(ent_labels[i], idx_dict)
        output[label_idx] += ' -- ' + replaced_chunks[i].text
    
    combined = ' '.join(output)
    # print(combined)
    return(combined)




if __name__ == "__main__":
    # sample = 'Background : Porcine reproductive and DISEASE ( DISEASE ) caused by PRRS virus ( DISEASE ) results in economic losses in the swine industry globally .'
    # doc = nlp(remove_sectionname(sample))
    # offsets = create_dict(doc)
    # print(bfs(doc, []))

    # l = 'Background : Porcine reproductive and DISEASE ( DISEASE ) caused by PRRS virus ( DISEASE ) results in economic losses in the swine industry globally .'
    # e = 'Background : Porcine reproductive and respiratory syndrome ( PRRS ) caused by PRRS virus ( PRRSV ) results in economic losses in the swine industry globally . "}'
    # doc_l = nlp(remove_sectionname(l))
    # doc_e = nlp(remove_sectionname(e))
    # print(link_entity(doc_e, doc_l))

    with open('./combined_data.jsonl', 'r') as json_file_labels:
        json_list_labels = list(json_file_labels)
    json_file_labels.close()

    with open('./original_data.jsonl', 'r') as json_file_ents:
        json_list_ents = list(json_file_ents)
    json_file_ents.close()

    # assert(len(json_list_labels) == len(json_file_ents))

    for i, j in enumerate(json_list_labels):
        json_dict_labels = json.loads(json_list_labels[i])
        json_dict_ents = json.loads(json_list_ents[i])
        text_labels = remove_sectionname(json_dict_labels['text'])
        text_ents = remove_sectionname(json_dict_ents['text'])
        doc_labels = nlp(text_labels)
        doc_ents = nlp(text_ents)

        # extraction
        print(bfs(doc_labels, []))
        # combine label and entities
        print(link_entity(doc_labels, doc_ents))
        print('=====')