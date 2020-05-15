import re, jsonlines

def combine(gene_file, chem_file, disease_file, gene_drna_cell_file):

    sentences = []
    with open(gene_file, 'r', encoding='utf8') as g:
        with open(chem_file, 'r', encoding='utf8') as c:
            with open(disease_file, 'r', encoding='utf8') as d:
                with open(gene_drna_cell_file, 'r', encoding='utf8') as gdcf:
                    sent = ""
                    for gline, cline, dline, gdcfline in zip(g.readlines(),
                                                             c.readlines(), d.readlines(), gdcf.readlines()):
                        # append any tokens that were not labeled as entities in all the files
                        if gline[0:-1][-1] == 'O' and cline[0:-1][-1] == 'O' and dline[0:-1][-1] == 'O' and gdcfline[0:-1][-1] == 'O':
                            if gline.split()[0] != '.....':
                                sent += gline.split()[0] + ' '
                            else:   # reached sentence break indicator, break sentence
                                sentences.append(sent)
                                sent = ""
                                continue
                        if gline[0:-1][-1] != 'O':
                            label = gline.split()[1]
                            if len(label.split('-')) > 1:
                                sent += label.split('-')[1].upper() + ' '   # substitue named entity with its type GENE
                        if cline[0:-1][-1] != 'O':
                            label = cline.split()[1]
                            if len(label.split('-')) > 1:
                                sent += label.split('-')[1].upper() + ' '   # substitute named entity with its type CHEMICAL
                        if dline[0:-1][-1] != 'O':
                            label = dline.split()[1]
                            if len(label.split('-')) > 1:
                                sent += label.split('-')[1].upper() + ' '   # sub named eneity with its type DISEASE
                        if gdcfline[0:-1][-1] != 'O':
                            label = gdcfline.split()[1]
                            ignore_labels = ["GENE", 'DNA', 'RNA', 'CELL_LINE', 'CELL_TYPE']
                            if len(label.split('-')) > 1:
                                if label.split('-')[1].upper() not in ignore_labels:
                                    if sent[-5:] != "GENE ":
                                        sent += label.split('-')[1].upper() + ' '   # proteins that were not already labeled as GENE
                                    elif sent[-4:] not in ["DNA ", "RNA "]:
                                        sent += label.split('-')[1].upper() + ' '
                                    elif len(sent) > 8:
                                        if sent[-8:] != "DISEASE ":
                                            sent += label.split('-')[1].upper() + ' '
                                    elif len(sent) > 9:
                                        if sent[-9:] != "CHEMICAL ":
                                            sent += label.split('-')[1].upper() + ' '

    for _ in range(10):                   # print(sent)
        sentences = [re.sub(r"  +", " GENE ", x) for x in sentences]    # choose gene hyper of protein
        # sentences = [re.sub(r" CELL_TYPE DISEASE +", " DISEASE ", x) for x in sentences]    # disease hyper of cell_type
        # sentences = [re.sub(r" CELL_LINE DISEASE +", " DISEASE ", x) for x in sentences]    # disease hyper of gene
        sentences = [re.sub(r" DISEASE GENE +", " DISEASE ", x) for x in sentences]
        sentences = [re.sub(r" DISEASE GENE +", " DISEASE ", x) for x in sentences]
        sentences = [re.sub(r" PROTEIN GENE +", " GENE ", x) for x in sentences]    # choose gene hyper of protein
        sentences = [re.sub(r" GENE PROTEIN +", " GENE ", x) for x in sentences]    # choose gene hyper of protein
        sentences = [re.sub(r"GENE PROTEIN +", " GENE ", x) for x in sentences]    # choose gene hyper of protein
        sentences = [re.sub(r" GENE DISEASE +", " DISEASE ", x) for x in sentences]    # choose disease over gene
        sentences = [re.sub(r" DISEASE PROTEIN +", " DISEASE ", x) for x in sentences]    # choose disease hyper of protein
        sentences = [re.sub(r" GENE GENE +", " GENE ", x) for x in sentences]
        sentences = [re.sub(r" PROTEIN PROTEIN +", " PROTEIN ", x) for x in sentences]
        sentences = [re.sub(r" CHEMICAL PROTEIN +", " PROTEIN ", x) for x in sentences]
        sentences = [re.sub(r" CHEMICAL CHEMICAL +", " CHEMICAL ", x) for x in sentences]
        sentences = [re.sub(r" DISEASE DISEASE +", " DISEASE ", x) for x in sentences]
        sentences = [re.sub(r"DISEASE DISEASE +", " DISEASE ", x) for x in sentences]
        # remove paranthesis
        # sentences = [re.sub(r" \( GENE \) ", " ", x) for x in sentences]
        # sentences = [re.sub(r" \( PROTEIN \) ", " ", x) for x in sentences]
        # remove everything in paranthesis
        # sentences = [re.sub(r"\(.+\)", " ", x) for x in sentences]
        # sentences = [re.sub(r"\)", "", x) for x in sentences]
        # disease hyper of cell_type, cell_line, protein, gene, all labels
        # ignoring DNA, RNA label
        # including Cell_type, Cell_line
        # chemical over protein

    print(sentences)
    create_jsonl(sentences, 'combined_data.jsonl')

def create_jsonl(sentences, file_name):
        with jsonlines.open(file_name, mode='a') as writer:
            for sent in sentences:
                writer.write({"text": sent})


def get_original_text(gene_file):
    sentences = []
    with open(gene_file, 'r', encoding='utf8') as g:
        sent = ""
        for g_line in g.readlines():
            if g_line.split()[0] != ".....":
                sent += g_line.split()[0] + ' '
            else:
                sentences.append(sent)
                sent = ""

    create_jsonl(sentences, 'original_data.jsonl')


def main():
    gene_file = "./NER_data_output/break3_outputGENE.txt"
    chem_file = "./NER_data_output/break3_outputCHEMICAL.txt"
    disease_file = "./NER_data_output/break3_outputDISEASE.txt"
    gene_drna_cell_file = './NER_data_output/break3_outputGENE_DRNA_CELL.txt'

    # merge dataset entities from output NER files
    combine(gene_file, chem_file, disease_file, gene_drna_cell_file)
    # print raw text jsonl file of each sentence before labeling
    get_original_text(gene_file)

if __name__ == "__main__":
    main()