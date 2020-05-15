import glob, json, jsonlines
import random
from nltk import word_tokenize, sent_tokenize


def jsonl_file_create(glob_list):
    x = 0
    y = 0
    with jsonlines.open('100abstracts.jsonl', mode='a') as writer:
        for file in glob_list:
            if y == 100:
                break
            with open(file, encoding='utf8') as f:
                data = json.load(f)
                file_name = data['paper_id']
                full_abstract = ""
                for thing in data['abstract']:
                    full_abstract += thing['text'] + ' '
                if full_abstract:
                    if len(full_abstract) > 100:
                        y += 1
                        # print(full_abstract, '\n')
                        # writer.write({"id": x, "abstract": full_abstract})
                        writer.write({"text": full_abstract})
                        x += 1


def conLL_file_create(glob_list):
    x = 1
    y = 0
    with open('train_multiBIONER_subset.txt', 'a', encoding='utf8') as writer:
        for file in glob_list[:300]:
            if y == 100:
                break
            with open(file, encoding='utf8') as f:
                data = json.load(f)
                file_name = data['paper_id']
                full_abstract = ""
                for thing in data['abstract']:
                    full_abstract += thing['text'] + ' '
                if full_abstract:
                    if len(full_abstract) > 100:
                        y += 1
                        print("abstract: ", y)
                        toked_sents = sent_tokenize(full_abstract)
                        toked_sents = [word_tokenize(sent) for sent in toked_sents]
                        # print(toked_sents)
                        for sent in toked_sents:
                            print("sent:", x)
                            x += 1
                            for toke in sent:
                                writer.write(toke + '\n')
                            writer.write('.....\n')


def main():
    glob_list = glob.glob("./comm_use_subset/pdf_json/*.json")  # common use pdf_json files directory
    random.shuffle(glob_list)
    jsonl_file_create(glob_list)
    conLL_file_create(glob_list)


if __name__ == "__main__":
    main()
