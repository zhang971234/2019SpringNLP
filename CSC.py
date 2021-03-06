import re
import jieba
import json
import jieba.posseg as pseg

from bs4 import BeautifulSoup
from word2vec_lm import*

from snownlp import SnowNLP
from argparse import ArgumentParser
from LM_API import *

def is_chinese(char):
    if char >= '\u4e00' and char <= '\u9fa5':
            return True
    else:
            return False

# format: dict {'id' : {'text': str, 'answer': [[pos, char], [pos, char]]}}
def process_data_7(text_name, gt_name, save_name, simple):
    data = {}
    with open(text_name, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            pattern = r'(NID=[0-9]+)'
            id = re.search(pattern, line).group(0)[-5:]
            text = ''.join(line.split()[1:])
            if simple:
                if len(text) != len(SnowNLP(text).han):
                    text = "想一想，台北也是我们每天在待的地方，每天在这个大都市来回穿梭，自由走动，但我们可能也不会到公车站牌旁的小巷子里有些什么，或许有一窝狗、猫，在天桥下，又有什么，或许有着一群游名，或者是一群热爱极限运动的舞者，脚踏车、滑板玩家，这些东西都等着我们去发现。"
                else:
                    text = SnowNLP(text).han
            data[id] = {'text': text}
        assert len(data.items()) == 1000
    with open(gt_name, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip().split(', ')
            answer = []
            # extract wrong word id and replaced word
            for i in range(1, len(line), 2):
                if simple:
                    line[i + 1] = SnowNLP(line[i+1]).han
                answer.append([int(line[i]), line[i+1]])
            data[line[0]]['answer'] = answer
        assert len(data.items()) == 1000
    with open(save_name, 'w', encoding='utf-8') as f:
        json.dump(data, f)

# format: dict {'id' : {'text': str, 'answer': [[pos, char], [pos, char]]}}
def process_data_8(text_name, gt_name, save_name, simple):
    data = {}
    with open(text_name, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            id = line.split()[0][5:-1]
            text = ''.join(line.split()[1:])
            if simple:
                if len(text) != len(SnowNLP(text).han):
                    print(text)
                    han = list(SnowNLP(text).han)
                    new_han = []
                    k = 0
                    for i in range(len(han)):
                        if i < k:
                            continue
                        if i+3 < len(han) and han[i:i+4] == ['公', '共', '汽', '车']:
                            new_han += ['公', '车']
                            k = i + 4
                        else:
                            new_han += han[i]
                    new_text = ''.join(new_han)
                    if len(text) != len(new_text):
                        han = list(new_text)
                        new_han = []
                        k = 0
                        for i in range(len(han)):
                            if i < k:
                                continue
                            if i + 2 < len(han) and han[i:i + 3] == ['出', '租', '车']:
                                new_han += ['的', '士']
                                k = i + 3
                            else:
                                new_han += han[i]
                        new_text = ''.join(new_han)
                        print(new_text)
                        if len(text) != len(new_text):
                            han = list(new_text)
                            new_han = []
                            k = 0
                            for i in range(len(han)):
                                if i < k:
                                    continue
                                if i + 2 < len(han) and han[i:i + 3] == ['因', '特', '网']:
                                    new_han += ['网', '际', '网', '络']
                                    k = i + 3
                                else:
                                    new_han += han[i]
                            new_text = ''.join(new_han)
                            print(new_text)
                    assert len(text) == len(new_text)
                    text = new_text
                else:
                    text = SnowNLP(text).han
            data[id] = {'text': text}
    with open(gt_name, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip().split(', ')
            answer = []
            # extract wrong word id and replaced word
            if line[1] == '0':
                data[line[0]]['answer'] = []
            else:
                for i in range(1, len(line), 2):
                    if simple:
                        line[i + 1] = SnowNLP(line[i+1]).han
                    answer.append([int(line[i]), line[i+1]])
                data[line[0]]['answer'] = answer
    with open(save_name, 'w', encoding='utf-8') as f:
        json.dump(data, f)

# find sentence and corrention for sighan8 training data
def add_dict_data_8_train(data, soup):
    essays = soup.find_all('essay')
    for essay in essays:
        text = essay.find('text')
        passages = text.find_all('passage')
        for passage in passages:
            id = passage.attrs['id']
            sent = passage.string
            text = SnowNLP(sent).han
            if len(text) != len(text):
                print(sent, text)
                continue
            data[id] = {}
            data[id]['text'] = text
            data[id]['answer'] = []
        mistakes = essay.find_all('mistake')
        for mistake in mistakes:
            id = mistake.attrs['id']
            loc = int(mistake.attrs['location'])
            wrong = mistake.wrong.string
            correct = mistake.correction.string
            wrong = SnowNLP(wrong).han
            correct = SnowNLP(correct).han
            # print(str(wrong), data[id]['text'])
            try:
                start = data[id]['text'].index(str(wrong))
                data[id]['answer'].append([loc, correct[loc - start - 1]])
            except:
                if id in data.keys():
                    data.pop(id)
        print(id)
    return data

# format: dict {'id' : {'text': str, 'answer': [[pos, char], [pos, char]]}}
def process_data_8_train(text_name, save_name, simple):
    data = {}
    with open(text_name, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, "lxml")
    add_dict_data_8_train(data, soup)
    with open('data/sighan8csc_release1.0/Training/SIGHAN15_CSC_B2_Training.sgml', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, "lxml")
    add_dict_data_8_train(data, soup)

    print(len(data.keys()))
    with open(save_name, 'w', encoding='utf-8') as f:
        json.dump(data, f)

# format: list [word1, word2, ...]
def process_dict(dict_path, save_path, simple):
    dict = []
    with open(dict_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip().split()
            if line[0][0] != '#' and line[0][0] != '%':
                if simple:
                    dict.append(line[1])
                else:
                    dict.append(line[0])
        print(len(dict))
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(dict, f)

# format: dict {'char1': [char1-1, char1-2, ...], 'char2': [char2-1, ...], ...}
def process_cfs(cfs_pro_path, cfs_shape_path, save_path, simple):
    dict = {}
    with open(cfs_pro_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip().split()
            key = SnowNLP(line[0]).han
            value = ''.join(line[1:])
            try:
                if simple:
                    value = SnowNLP(value).han
            except:
                pass
            value = list(value)
            dict[key] = value
    with open(cfs_shape_path, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip().split(',')
            try:
                key = SnowNLP(line[0]).han
            except:
                continue
            value = ''.join(line[1:])
            if simple:
                value = SnowNLP(value).han
            value = list(value)
            if key in dict.keys():
                dict[key] += value
            else:
                dict[key] = value
        print(len(dict.items()))
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(dict, f)

# format: dict {'id' : {'text': str, 'answer': [[pos, char], [pos, char]], 'seg': [a, b, c], 'pos': [n, v, adj], 'len': [2, 1, 2], 'label': [12, 23]}}
def data_seg(data_json, save_json):
    with open(data_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    near_count = 0
    for k,v in data.items():
        seg_list = jieba.lcut(v['text'], HMM=False)
        len_list = [len(word) for word in seg_list]
        words = pseg.cut(v['text'], HMM=False)
        pos = [word.flag for word in words]
        answer_index = [p[0] for p in v['answer']]
        answer_index = sorted(answer_index)
        for i, index in enumerate(answer_index):
            if i > 0 and answer_index[i] - answer_index[i-1] < 3:
                near_count += 1
        label_index = []
        index = 1
        answer_p = 0
        if answer_index:
            for i, word in enumerate(seg_list):
                if index <= answer_index[answer_p] and index + len(word) > answer_index[answer_p]:
                    label_index.append(i)
                    answer_p += 1
                    if answer_p == len(answer_index):
                        break
                index += len(word)

        data[k]['seg'] = seg_list
        data[k]['pos'] = pos
        data[k]['len'] = len_list
        data[k]['label'] = label_index
        assert len(seg_list) == len(pos)
    with open(save_json, 'w', encoding='utf-8') as f:
        json.dump(data, f)

# format: dict {'id' : {'text': str, 'answer': [[1, 我], [2, 是]], 'cand': [[[1, [我, 你]]], [[2, [没, 有]], [3, [好]]]]}}
def make_candidate(data, vocab_dict, cfs_dict, save_path, config):
    total_count, tmp_count, total_chars = 0., 0, 0.
    total_sent = len(data.keys())
    for k, v in data.items():
        sample = v
        total_chars += len(sample['text'])
        seg_list = jieba.lcut(sample['text'], HMM=False)
        index = 1
        answer_index = [p[0] for p in sample['answer']]
        total_count += len(answer_index)
        candidates = []
        last_index = 0
        for i, word in enumerate(seg_list):
            # numerate all candidates
            if config.cand_choose == 'single':
                if len(word) == 1 and is_chinese(word) and sample['text'][index - 1] in cfs_dict.keys():
                    # two consecutive single characters
                    if i == 0:
                        if len(seg_list[i + 1]) == 1:
                            candidates.append([[index, cfs_dict[sample['text'][index - 1]]]])
                    elif i == len(seg_list) - 1:
                        if len(seg_list[i - 1]) == 1:
                            candidates.append([[index, cfs_dict[sample['text'][index - 1]]]])
                    else:
                        if len(seg_list[i + 1]) == 1 or len(seg_list[i - 1]) == 1:
                            candidates.append([[index, cfs_dict[sample['text'][index - 1]]]])
                # word with 2 chars but not in given dictionary
                if len(word) == 2 and word not in vocab_dict:
                    all_cand = []
                    if sample['text'][index - 1] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index - 1]]:
                            if cand + sample['text'][index] in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index, candidate])
                    if sample['text'][index] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index]]:
                            if sample['text'][index - 1] + cand in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index+1, candidate])
                    if all_cand:
                        candidates.append(all_cand)
                if len(word) == 3 and word not in vocab_dict:
                    all_cand = []
                    if sample['text'][index - 1] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index - 1]]:
                            if cand + sample['text'][index] + sample['text'][index + 1] in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index, candidate])
                    if sample['text'][index] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index]]:
                            if sample['text'][index - 1] + cand + sample['text'][index + 1] in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index+1, candidate])
                    if sample['text'][index + 1] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index + 1]]:
                            if sample['text'][index - 1] + sample['text'][index] + cand in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index+2, candidate])
                    if all_cand:
                        candidates.append(all_cand)
            # correct only one char in given consective single chars
            elif config.cand_choose == 'consec':
                if i < last_index:
                    continue
                if len(word) == 1 and is_chinese(word):
                    j = i + 1
                    while True:
                        if j < len(seg_list) and len(seg_list[j]) == 1 and is_chinese(seg_list[j]):
                            j += 1
                        else:
                            break
                    # [i, j] are consecutive single char
                    if j - i > 1:
                        all_cands = []
                        for m in range(i, j):
                            if seg_list[m] in cfs_dict.keys():
                                all_cands.append([index, cfs_dict[seg_list[m]]])
                            index += 1
                        if all_cands:
                            candidates.append(all_cands)
                    else:
                        index += 1
                    last_index = j
                    continue
                if len(word) == 2 and word not in vocab_dict:
                    all_cand = []
                    if sample['text'][index - 1] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index - 1]]:
                            if cand + sample['text'][index] in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index, candidate])
                    if sample['text'][index] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index]]:
                            if sample['text'][index - 1] + cand in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index+1, candidate])
                    if all_cand:
                        candidates.append(all_cand)
                if len(word) == 3 and word not in vocab_dict:
                    all_cand = []
                    if sample['text'][index - 1] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index - 1]]:
                            if cand + sample['text'][index] + sample['text'][index + 1] in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index, candidate])
                    if sample['text'][index] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index]]:
                            if sample['text'][index - 1] + cand + sample['text'][index + 1] in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index+1, candidate])
                    if sample['text'][index + 1] in cfs_dict.keys():
                        candidate = []
                        for cand in cfs_dict[sample['text'][index + 1]]:
                            if sample['text'][index - 1] + sample['text'][index] + cand in vocab_dict:
                                candidate.append(cand)
                        if candidate:
                            all_cand.append([index+2, candidate])
                    if all_cand:
                        candidates.append(all_cand)
            index += len(word)
        tmp_count += 1
        print(k, ' ', tmp_count, '/', total_sent)
        data[k]['cand'] = candidates

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)

# make condidate of SVM mistake detector
def make_candidate_SVM(data, seg_data, result, cfs_dict, save_path, config):
    for k, v in data.items():
        cands = []
        seg_text = seg_data[k]['seg']
        cand_index = result[k]
        pos = 1
        pos_index = []
        for word in seg_text:
            pos_index.append(pos)
            pos += len(word)
        for index in cand_index:
            cand = []
            for i, word in enumerate(seg_text[index]):
                if word in cfs_dict.keys():
                    cand.append([pos_index[index]+i, cfs_dict[word]])
            if cand:
                cands.append(cand)
        data[k]['cand'] = cands

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)

# format: dict={'id': {'res': [[1, 我], [2, 你]]}}
def get_result(data_json, save_file, embed, lm_choose):
    with open(data_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for k,v in data.items():
        v['res'] = []
        org_text = v['text']
        #print('\n 原文本：', org_text, jieba.lcut(org_text, HMM=False))
        for sample in v['cand']:
            # [[1, [我, 你]], [2, [好]]]
            sample_index = [p[0] for p in sample]
            left_index = max(min(sample_index) - 3, 1)
            right_index = min(max(sample_index) + 3, len(org_text))
            if lm_choose == '3-gram':
                org_score = LM_score([org_text[left_index - 1:right_index]])[0]
                max_score = org_score * 10
            else:
                org_score = SentScore(embed, org_text[left_index-1:right_index])
                max_score = org_score + 5
            cand_res = None
            for pos_cand in sample:
                new_text = list(org_text)
                for cand in pos_cand[1]:
                    new_text[pos_cand[0] - 1] = cand
                    if lm_choose == '3-gram':
                        new_score = LM_score([''.join(new_text[left_index - 1:right_index])])[0]
                    else:
                        new_score = SentScore(embed, ''.join(new_text[left_index - 1:right_index]))
                    if new_score > max_score:
                        max_score = new_score
                        try:
                            #cand_res = [org_text[pos_cand[0]-2:pos_cand[0]+1], cand]
                            cand_res = [pos_cand[0], cand]
                        except:
                            pass
            if cand_res:
                v['res'].append(cand_res)
                #print('最后替换结果： ', k, cand_res)
        #print('真实结果： ', v['answer'])
    with open(save_file, 'w', encoding='utf-8') as f:
        for k, v in data.items():
            line = k
            if v['res']:
                for cand in v['res']:
                    line += ', '+ str(cand[0]) + ', ' + cand[1]
            line += '\n'
            f.write(line)
    return data

# calculate evaluation metrics
def cal_metric(result):
    ctp, cfp, dtp, dfp, p = 0., 0., 0., 0., 0.
    for k,v in result.items():
        p += len(v['answer'])
        true_index = [ans[0] for ans in v['answer']]
        for cand in v['res']:
            if cand in v['answer']:
                ctp += 1
            else:
                cfp += 1
            if cand[0] in true_index:
                dtp += 1
            else:
                dfp += 1
    cp = ctp/(ctp + cfp)
    cr = ctp/p
    cf = (2 * cp * cr)/(cp + cr)
    dp = dtp/(dtp + dfp)
    dr = dtp/p
    df = (2 * dp * dr)/(dp + dr)
    res = {'cp': cp, 'cr': cr, 'cf': cf, 'dp': dp, 'dr': dr, 'df': df}
    print(res)
    print(ctp, ctp+cfp, p)
    return res

def get_args():
    parser = ArgumentParser(description='chinese spelling check')
    parser.add_argument('--test_text', type=str, default='data/sighan7csc_release1.0/FinalTest_/FinalTest_SubTask2.txt')
    #parser.add_argument('--test_text', type=str, default='data/sighan8csc_release1.0/Test/SIGHAN15_CSC_TestInput.txt')
    parser.add_argument('--test_gt', type=str, default='data/sighan7csc_release1.0/FinalTest_/FinalTest_SubTask2_Truth.txt')
    parser.add_argument('--data_json', type=str,
                        default='data/sighan7_simple.json')
    parser.add_argument('--dict', type=str, default='data/cedict_ts.u8')
    parser.add_argument('--dict_json', type=str, default='data/chinese_dict_simple.json')
    parser.add_argument('--cfs_pro', type=str,
                        default='data/sighan7csc_release1.0/ConfusionSet/Bakeoff2013_CharacterSet_SimilarPronunciation.txt')
    parser.add_argument('--cfs_shape', type=str,
                        default='data/sighan7csc_release1.0/ConfusionSet/Bakeoff2013_CharacterSet_SimilarShape.txt')
    parser.add_argument('--cfs_dict', type=str, default='data/confusion_set_simple.json')
    parser.add_argument('--simple', type=bool, default=True)
    parser.add_argument('--data_seg_json', type=str, default='data/sighan7_seg_simple.json')
    parser.add_argument('--data_cand_json', type=str, default='data/candidate/sighan7.json')
    parser.add_argument('--cand_choose', type=str, default='single')
    parser.add_argument('--lm_choose', type=str, default='3-gram')
    parser.add_argument('--lm', type=str, default='data/sgns.baidubaike.bigram-char')
    parser.add_argument('--res_svm', type=str, default='data/test_result_sighan8.json')
    parser.add_argument('--save_file', type=str, default='result/sighan7.txt')
    args = parser.parse_args()
    return args

def main():
    config = get_args()
    #process_data_7(config.test_text, config.test_gt, config.data_json, config.simple)
    #process_data_8(config.test_text, config.test_gt, config.data_json, config.simple)
    #process_data_8_train(config.test_text, config.data_json, config.simple)
    #process_dict(config.dict, config.dict_json, config.simple)
    #process_cfs(config.cfs_pro, config.cfs_shape, config.cfs_dict, config.simple)
    #data_seg(config.data_json, config.data_seg_json)
    with open(config.cfs_dict, 'r', encoding='utf-8') as f:
        cfs_dict = json.load(f)
    with open(config.dict_json, 'r', encoding='utf-8') as f:
        vocab_dict = json.load(f)
    with open(config.data_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(config.data_seg_json, 'r', encoding='utf-8') as f:
        seg_data = json.load(f)
    with open(config.res_svm, 'r', encoding='utf-8') as f:
        res_svm = json.load(f)
    config.data_cand_json = config.data_cand_json[:-5] + '_' + config.cand_choose + '_' + config.lm_choose + '.json'
    if config.cand_choose == 'svm':
        make_candidate_SVM(data, seg_data, res_svm, cfs_dict, config.data_cand_json, config)
    else:
        make_candidate(data, vocab_dict, cfs_dict, config.data_cand_json, config)
    print("candidate name: ", config.data_cand_json)
    config.embeddings_index = getEmbed(config.lm)
    config.save_file = config.save_file[:-4] + '_' + config.cand_choose + '_' + config.lm_choose + '.txt'
    print("result name: ", config.save_file)
    result = get_result(config.data_cand_json, config.save_file, config.embeddings_index, config.lm_choose)
    result = cal_metric(result)

if __name__ == '__main__':
    main()