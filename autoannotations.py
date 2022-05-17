import nltk.tokenize as tk
from nltk.tokenize import wordpunct_tokenize
import subprocess
import jsonlines
import sys
import os
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--model", help="Path to the coref model")
args = parser.parse_args()
MODEL = args.model
TEMP_FILE = r'temp.txt'
OUT_FILE = r'out.txt'

text = input("Введите текст: ")
tempstring = ''
sentences = tk.sent_tokenize(text, language='russian')

templist = []
for sentence in sentences:
    inner_sent = wordpunct_tokenize(sentence)
    templist.append(inner_sent)

token_index = 0
for tokenized_sent in templist:
    tempstring += '\n'
    token_index = 0
    for token in tokenized_sent:
        tempstring += 'book0\t0\t' + str(token_index) + '\t' + token + '\t' + '_\t_\t_\t_\t_\t_\t-\n'
        token_index += 1
tempstring = '#begin document (book0); part 0' + tempstring + '\n' + '#end document'

with open(TEMP_FILE, 'w', encoding='utf-8') as tempfile:
    tempfile.write(tempstring)
    tempfile.close()

print('Loading and building the model...')
p = subprocess.run(["allennlp", "evaluate", f"{MODEL}", f"{TEMP_FILE}", "--predictions-output-file", f"{OUT_FILE}"], capture_output=True)

def get_mention(begin, text_list, all_cluster_tokens):
    for id, cluster in enumerate(all_cluster_tokens[0]):
        for i, token_set in enumerate(cluster):
            if begin == token_set[0]:
                mention_string = ''
                indexer = id
                if token_set[0]==token_set[-1]: #this means that the mention contains only one word
                    mention_string += text_list[token_set[0]] + ' '
                else:
                    token_set = [i for i in range(token_set[0], token_set[-1]+1)]
                    for offset in token_set:
                        mention_string += text_list[offset] + ' '
    modifier = '{' + cluster_uids[indexer] +  ': ' + mention_string + '}'
    return modifier

cluster_offsets = []
with jsonlines.open(OUT_FILE) as predicted_file:
    for line in predicted_file.iter():
      cluster_offsets.append(line['clusters'][0])

all_indices = []
for cluster_unit in cluster_offsets:
  for cluster in cluster_unit:
    for mention in cluster:
      for offset in range(mention[0], mention[1]+1):
        all_indices.append(offset)

number = len(cluster_offsets[0])
cluster_uids = [f'M{i+1}' for i in range(number+1)]

beginnings = []
for cluster in cluster_offsets[0]:
    local_beginnings = [i[0] for i in cluster]
    beginnings += local_beginnings

text_list = wordpunct_tokenize(text)
for idx, token in enumerate(text_list):
  if idx not in all_indices:
    print(token, end=' ')
  else:
    if idx in beginnings:
        mention = get_mention(idx, text_list, cluster_offsets)
        print(mention, end = ' ')
    else:
        pass

