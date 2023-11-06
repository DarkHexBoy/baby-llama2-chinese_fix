import json
import glob
import numpy as np
from tqdm import tqdm
import pandas as pd
import os
from datasets import load_dataset
from src.share import get_logger
from src.utils import *

GLOBAL_DATA_PATH = './data'
GLOBAL_MIN_LEN = 15
logger = get_logger(os.path.join(GLOBAL_DATA_PATH,'log.log'))


def process_CLUECorpusSmall(tokenizer, BATCH_SIZE, save_all_text = False):
    data_path = GLOBAL_DATA_PATH

    if check_is_processed(f'{GLOBAL_DATA_PATH}/pretrain_CLUECorpusSmall', data_path):
        print(f'pretrain_CLUECorpusSmall has been processed')
        return

    dataset_list= {
        'comment2019zh__corpus',
        'news2016zh_corpus',
        'webText2019zh_corpus2',
        'wiki_zh'
    }
    data_dict = dict()
    for data_name in dataset_list:
        data_dict[data_name] = getAllFiles(os.path.join(data_path, data_name))

    for key in data_dict:
        print(f'process CLUECorpusSmall {key}')

        if save_all_text:
            corpus_txts = open(f'./data/tokenizer_CLUECorpusSmall_{key}.txt', 'w', encoding='utf-8')

        doc_ids = []
        batch_cnt = 0
        total_id_len = 0
        for data_list in tqdm(data_dict[key]):
            f1 = open(data_list, 'r', encoding='utf-8')
            while True:
                line = f1.readline()
                if not line:
                    break
                if len(line) < GLOBAL_MIN_LEN:
                    continue

                if not data_list.endswith('txt'):
                    line = json.loads(line)
                    line = line['text']

                if tokenizer is not None:
                    text_id = tokenizer.encode(line, add_special_tokens=False)
                    text_id.append(tokenizer.special_tokens['<eos>'])
                    if len(text_id) < GLOBAL_MIN_LEN:
                        continue

                    doc_ids += text_id
                    total_id_len += len(text_id)
                    
                if save_all_text:
                    corpus_txts.write(line)

                if len(doc_ids) > 0 and len(doc_ids) > BATCH_SIZE:
                    arr = np.array(doc_ids, dtype=np.uint16)
                    with open(f'{data_path}/pretrain_CLUECorpusSmall_{key}_{batch_cnt}.bin', 'wb') as f:
                        f.write(arr.tobytes())
                    batch_cnt += 1
                    doc_ids = []
                    del arr

        if len(doc_ids) > 0:
            arr = np.array(doc_ids, dtype=np.uint16)
            with open(f'{data_path}/pretrain_CLUECorpusSmall_{key}_{batch_cnt}.bin', 'wb') as f:
                f.write(arr.tobytes())
        print(f'processed CLUECorpusSmall_{key} tokens: {total_id_len}')
        logger.info(f'processed CLUECorpusSmall_{key} tokens: {total_id_len}')

        if save_all_text:
            corpus_txts.close()


def process_baidu(data_path, tokenizer, BATCH_SIZE, save_all_text=False):
    batch_cnt = 0
    doc_ids = []
    data_path = GLOBAL_DATA_PATH

    if check_is_processed(f'{GLOBAL_DATA_PATH}/pretrain_baidubaike_563w', data_path):
        print(f'baidubaike_563w has been processed')
        return

    if save_all_text:
        corpus_txts = open(f'./data/tokenizer_baidubaike_563w.txt', 'w', encoding='utf-8')

    if not os.path.exists(data_path):
        print(
            f'{data_path} is not exist. please download from: https://huggingface.co/datasets/xuqinyang/BaiduBaike-5.63M/blob/main/563w_baidubaike.json')
        return

    f1 = open(data_path, 'r', encoding='utf-8')
    total_id_len = 0
    while True:
        line = f1.readline()
        if not line:
            break
        line = json.loads(line)
        text = ''
        try:
            text += line['title'] + ': ' + line['summary']
        except:
            pass
        for per in line['sections']:
            text += per['title'] + ': ' + per['content'] + '。'
        if tokenizer is not None:
            text_id = tokenizer.encode(text, add_special_tokens=False)
            text_id.append(tokenizer.special_tokens['<eos>'])
            if len(text_id) < GLOBAL_MIN_LEN:
                continue
            doc_ids += text_id
            total_id_len+=len(text_id)

        if save_all_text:
            corpus_txts.write(text + '\n')

        if len(doc_ids) > 0 and len(doc_ids) > BATCH_SIZE:
            arr = np.array(doc_ids, dtype=np.uint16)
            with open(f'{data_path}/pretrain_baidubaike_563w_{batch_cnt}.bin', 'wb') as f2:
                f2.write(arr.tobytes())
            batch_cnt += 1
            doc_ids = []
            del arr

    if len(doc_ids) > 0:
        arr = np.array(doc_ids, dtype=np.uint16)
        with open(f'{data_path}/pretrain_baidubaike_563w_{batch_cnt}.bin', 'wb') as f:
            f.write(arr.tobytes())

    if save_all_text:
        corpus_txts.close()

    print(f'processed baidubaike_563w tokens: {total_id_len}')
    logger.info(f'processed baidubaike_563w tokens: {total_id_len}')


# from zhconv import convert
def process_wiki_zh_clean(tokenizer, wiki_data_path, save_all_text=False):
    data_path = GLOBAL_DATA_PATH
    if check_is_processed(f'{GLOBAL_DATA_PATH}/pretrain_wiki_zh', data_path):
        print(f'pretrain_wiki_zh has been processed')
        return

    if not os.path.exists(wiki_data_path):
        print(
            f'{wiki_data_path} is not exist. please download from: https://huggingface.co/datasets/pleisto/wikipedia-cn-20230720-filtered/blob/main/wikipedia-cn-20230720-filtered.json')
        return

    if save_all_text:
        corpus_txts = open(f'./data/tokenizer_wiki_zh_clean.txt', 'w', encoding='utf-8')

    with open(wiki_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    doc_ids = []
    total_id_len=0
    for line in tqdm(data):
        text = line['completion']
        if tokenizer is not None:
            text_id = tokenizer.encode(text, add_special_tokens=False)
            text_id.append(tokenizer.special_tokens['<eos>'])
            if len(text_id) > GLOBAL_MIN_LEN:
                doc_ids += text_id
                total_id_len += len(text_id)
        if save_all_text:
            corpus_txts.write(text + '\n')

    if len(doc_ids) > 0:
        arr = np.array(doc_ids, dtype=np.uint16)
        with open(f'{data_path}/pretrain_wiki.bin', 'wb') as f:
            f.write(arr.tobytes())

    if save_all_text:
        corpus_txts.close()

    print(f'processed pretrain_wiki_zh tokens: {total_id_len}')
    logger.info(f'processed pretrain_wiki_zh tokens: {total_id_len}')


def process_wiki(tokenizer, BATCH_SIZE, save_all_text=False):
    data_date = '20220301'
    data_type = 'en'
    batch_cnt = 0
    data_path = GLOBAL_DATA_PATH

    dateset_path = f'{data_path}/pretrain_wikipedia_{data_date}_{data_type}_{batch_cnt}.bin'
    if os.path.exists(dateset_path):
        return

    if save_all_text:
        corpus_txts = open(f'./data/tokenizer_wikipedia.txt', 'w', encoding='utf-8')

    wiki_data = load_dataset("wikipedia", f"{data_date}.{data_type}")

    doc_ids = []
    total_id_len = 0
    for line in tqdm(wiki_data):
        for paragraph in line['段落']:
            # rr=line['response_rejected']
            if tokenizer is not None:
                content_id = tokenizer.encode(paragraph['内容'], add_special_tokens=False)
                # rr_id=tokenizer.encode(rr,add_special_tokens=False)
                text_id = content_id + [tokenizer.special_tokens['<eos>']]
                if len(text_id) > GLOBAL_MIN_LEN:
                    doc_ids += text_id
                    total_id_len += len(text_id)
            if save_all_text:
                corpus_txts.write(paragraph['内容'] + '\n')


        if len(doc_ids) > 0 and len(doc_ids) > BATCH_SIZE:
            arr = np.array(doc_ids, dtype=np.uint16)
            target_p = dateset_path.replace(f'{0}.bin', f'{batch_cnt}.bin')
            with open(target_p, 'wb') as f:
                f.write(arr.tobytes())
            batch_cnt += 1
            doc_ids = []
            del arr

    if len(doc_ids) > 0:
        arr = np.array(doc_ids, dtype=np.uint16)
        target_p = dateset_path.replace(f'{0}.bin', f'{batch_cnt}.bin')
        with open(target_p, 'wb') as f:
            f.write(arr.tobytes())

    if save_all_text:
        corpus_txts.close()

    print(f'processed pretrain_wiki tokens: {total_id_len}')
    logger.info(f'processed pretrain_wiki tokens: {total_id_len}')


def process_wiki_en(tokenizer, BATCH_SIZE, save_all_text=False):
    data_path = GLOBAL_DATA_PATH
    batch_cnt = 0
    dateset_path = f'{data_path}/pretrain_tdtunlp_wikipedia_en_{batch_cnt}.bin'
    if os.path.exists(dateset_path):
        return

    if save_all_text:
        corpus_txts = open(f'./data/tokenizer_wikipedia_en.txt', 'w', encoding='utf-8')

    wiki_data = load_dataset("tdtunlp/wikipedia_en")
    doc_ids = []
    total_id_len = 0
    for paragraph in tqdm(wiki_data['train']):
        for line in paragraph['text'].split('\n'):
            # rr=line['response_rejected']
            if len(line) < GLOBAL_MIN_LEN:
                continue

            if tokenizer is not None:
                content_id = tokenizer.encode(line, add_special_tokens=False)
                # rr_id=tokenizer.encode(rr,add_special_tokens=False)
                text_id = content_id + [tokenizer.special_tokens['<eos>']]
                if len(text_id) < GLOBAL_MIN_LEN:
                    continue
                doc_ids += text_id
                total_id_len += len(text_id)

            if save_all_text:
                corpus_txts.write(line + '\n')


            if len(doc_ids) > 0 and len(doc_ids) > BATCH_SIZE:
                arr = np.array(doc_ids, dtype=np.uint16)
                target_p = dateset_path.replace(f'{0}.bin', f'{batch_cnt}.bin')
                with open(target_p, 'wb') as f:
                    f.write(arr.tobytes())
                batch_cnt += 1
                doc_ids = []
                del arr

    if len(doc_ids) > 0:
        arr = np.array(doc_ids, dtype=np.uint16)
        target_p = dateset_path.replace(f'{0}.bin', f'{batch_cnt}.bin')
        with open(target_p, 'wb') as f:
            f.write(arr.tobytes())

    if save_all_text:
        corpus_txts.close()

    print(f'processed pretrain_tdtunlp_wikipedia_en tokens: {total_id_len}')
    logger.info(f'processed pretrain_tdtunlp_wikipedia_en tokens: {total_id_len}')


def process_MNBVC_clean(tokenizer, BATCH_SIZE, save_all_text=False):
    # https://huggingface.co/datasets/liwu/MNBVC
    dataset_list = {
        # 'law_judgement',       # 法律
        # 'gov_xuexiqiangguo',   # 学习强国
        # 'gov_report',          # 政府工作报告
        # 'co_ann_report',       # 企业年报
        # 'code_metadata',       # 代码元数据
        'qa_zhihu',  # 知乎的问答
        # 'qa_wikihow:',         # wikihow的问答  好像不存在??
        # 'qa_mfa:',             # 外交部问答数据
        # 'news_peoples_daily',  # 人民日报的文本
        # 'wikipedia',           # 维基百科的文本
        'qa_stackexchange',  # StackExchange的问答
        'qa_chatgpt',  # ChatGPT构造的问答语料
        # 'math_qa',             # 数学领域有关的问答
        # 'math_chat',           # 数学领域有关的对话数据数据，可以提升模型Chain of Thought的能力
        'crawler_oscar',  # 从CommonCrawl中清洗出来的通用文本数据
    }

    if save_all_text:
        corpus_txts = open(f'./data/tokenizer_MNBVC_clean.txt', 'w', encoding='utf-8')

    data_path = GLOBAL_DATA_PATH
    for dataset_name in dataset_list:
        dateset_path = f'{data_path}/pretrain_mnbvc_{dataset_name}.bin'
        target_p = dateset_path.replace('.bin', f'_{0}.bin')
        if not os.path.exists(target_p):
            total_id_len = 0
            try:
                batch_cnt = 0
                print(f'load [MNBVC] {dataset_name}')
                dataset = load_dataset("liwu/MNBVC", dataset_name, split='train', streaming=True)
                doc_ids = []

                if 'crawler_oscar' == dataset_name:
                    for line in tqdm(dataset):
                        # next(iter(dataset))  # get the first line
                        for paragraph in line['段落']:
                            # rr=line['response_rejected']
                            if tokenizer is not None:
                                content_id = tokenizer.encode(paragraph['内容'], add_special_tokens=False)
                                # rr_id=tokenizer.encode(rr,add_special_tokens=False)
                                text_id = content_id + [tokenizer.special_tokens['<eos>']]
                                if len(text_id) > GLOBAL_MIN_LEN:
                                    doc_ids += text_id
                                    total_id_len += len(text_id)

                            if save_all_text:
                                corpus_txts.write(paragraph['内容'] + '\n')

                        if len(doc_ids) > 0 and len(doc_ids) > BATCH_SIZE:
                            arr = np.array(doc_ids, dtype=np.uint16)
                            target_p = dateset_path.replace('.bin', f'_{batch_cnt}.bin')
                            with open(target_p, 'wb') as f:
                                f.write(arr.tobytes())
                            batch_cnt += 1
                            doc_ids = []
                            del arr
                else:
                    for line in tqdm(dataset):
                        # next(iter(dataset))  # get the first line
                        q = line['问']
                        rc = line['答']
                        # rr=line['response_rejected']
                        if tokenizer is not None:
                            q_id = tokenizer.encode(q, add_special_tokens=False)
                            rc_id = tokenizer.encode(rc, add_special_tokens=False)
                            # rr_id=tokenizer.encode(rr,add_special_tokens=False)
                            text_id = q_id + rc_id + [tokenizer.special_tokens['<eos>']]
                            if len(text_id) < GLOBAL_MIN_LEN:
                                continue
                            doc_ids += text_id
                            total_id_len += len(text_id)

                        if save_all_text:
                            corpus_txts.write(q + rc + '\n')

                        if len(doc_ids) > 0 and len(doc_ids) > BATCH_SIZE:
                            arr = np.array(doc_ids, dtype=np.uint16)
                            target_p = dateset_path.replace('.bin', f'_{batch_cnt}.bin')
                            with open(target_p, 'wb') as f:
                                f.write(arr.tobytes())
                            batch_cnt += 1
                            doc_ids = []
                            del arr

                if len(doc_ids) > 0:
                    arr = np.array(doc_ids, dtype=np.uint16)
                    target_p = dateset_path.replace('.bin', f'_{batch_cnt}.bin')
                    with open(target_p, 'wb') as f:
                        f.write(arr.tobytes())
            except:
                print(f'dowload {dateset_path} error....')
        else:
            print(f'{dateset_path} has been processed')

    if save_all_text:
        corpus_txts.close()

    print(f'processed process_MNBVC_clean tokens: {total_id_len}')
    logger.info(f'processed process_MNBVC_clean tokens: {total_id_len}')


def process_medical(file_path, name, tokenizer, save_all_text=False):
    data_path = GLOBAL_DATA_PATH
    if check_is_processed(f'{data_path}/pretrain_medical_{name}.bin',data_path):
        print(f'pretrain_medical has been processed')
        return

    if not os.path.exists(file_path):
        print(
            f'{file_path} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical/blob/main/pretrain/medical_book_zh.json')
        return

    if save_all_text:
        corpus_txts = open(f'{GLOBAL_DATA_PATH}//tokenizer_medical_{name}.txt', 'w', encoding='utf-8')

    f = open(file_path, 'r', encoding='utf-8')
    doc_ids = []
    total_id_len = 0
    while True:
        line = f.readline()
        if not line:
            break
        line = json.loads(line)
        text = line['text']
        
        if tokenizer is not None:
            text_id = tokenizer.encode(text, add_special_tokens=False)
            text_id.append(tokenizer.special_tokens['<eos>'])
            if len(text_id) > GLOBAL_MIN_LEN:
                doc_ids += text_id
                total_id_len += len(text_id)

        if save_all_text:
            corpus_txts.write(text + '\n')

    if len(doc_ids) > 0:
        arr = np.array(doc_ids, dtype=np.uint16)
        with open(f'{data_path}/pretrain_medical_{name}.bin', 'wb') as f:
            f.write(arr.tobytes())

    if save_all_text:
        corpus_txts.close()

    print(f'processed process_medical tokens: {total_id_len}')
    logger.info(f'processed process_medical tokens: {total_id_len}')


def process_medical_qa(tokenizer, save_all_text=False):
    data_path = GLOBAL_DATA_PATH
    if check_is_processed(f'{GLOBAL_DATA_PATH}/pretrain_medical_qa.bin',data_path):
        print(f'pretrain_medical_qa has been processed')
        return

    doc_ids = []

    if save_all_text:
        corpus_txts = open(f'./data/tokenizer_medical_qa.txt', 'w', encoding='utf-8')

    print('process_medical_qa: train')
    data_name = f'{data_path}/train.json'
    total_id_len = 0
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['question']
                rc = line['response_chosen']
                # rr=line['response_rejected']
                
                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    rc_id = tokenizer.encode(rc, add_special_tokens=False)
                    # rr_id=tokenizer.encode(rr,add_special_tokens=False)
                    text_id = q_id + rc_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)

                if save_all_text:
                    corpus_txts.write(q + rc + '\n')

    print('process_medical_qa: train_en_1')
    data_name = f'{data_path}/train_en_1.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['input']
                a = line['output']

                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    a_id = tokenizer.encode(a, add_special_tokens=False)
                    text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(q + a + '\n')

    print('process_medical_qa: train_zh_0')
    data_name = f'{data_path}/train_zh_0.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(f'{data_path}/train_zh_0.json', 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['instruction'] + line['input']
                a = line['output']
                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    a_id = tokenizer.encode(a, add_special_tokens=False)
                    text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(q + a + '\n')

    print('process_medical_qa: train_encyclopedia')
    data_name = f'{data_path}/train_encyclopedia.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                text = line['text']
                if tokenizer is not None:
                    text_id = tokenizer.encode(text, add_special_tokens=False)
                    text_id.append(tokenizer.special_tokens['<eos>'])
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(text+ '\n')

    if len(doc_ids) > 0:
        arr = np.array(doc_ids, dtype=np.uint16)
        print(arr.shape)
        with open(f'{data_path}/pretrain_medical_qa.bin', 'wb') as f:
            f.write(arr.tobytes())

    if save_all_text:
        corpus_txts.close()

    print(f'processed pretrain_medical_qa tokens: {total_id_len}')
    logger.info(f'processed pretrain_medical_qa tokens: {total_id_len}')


def process_valid_medical(tokenizer, save_all_text=False):
    data_path = GLOBAL_DATA_PATH
    if check_is_processed(f'{data_path}/valid_data.bin',data_path):
        print(f'valid_data has been processed')
        return

    doc_ids = []
    total_id_len = 0

    if save_all_text:
        corpus_txts = open(f'{data_path}/tokenizer_valid_medical.txt', 'w', encoding='utf-8')

    print('valid_medical: valid')
    data_name = f'{data_path}/valid.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['question']
                rc = line['response_chosen']
                rr = line['response_rejected']
                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    rc_id = tokenizer.encode(rc, add_special_tokens=False)
                    rr_id = tokenizer.encode(rr, add_special_tokens=False)
                    text_id = q_id + rc_id + rr_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(q + rc + '\n')

    print('valid_medical: valid_en_1')
    data_name = f'{data_path}/valid_en_1.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['input']
                a = line['output']
                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    a_id = tokenizer.encode(a, add_special_tokens=False)
                    text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(q +  a + '\n')

    print('valid_medical: valid_zh_0')
    data_name = f'{data_path}/valid_zh_0.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['instruction'] + line['input']
                a = line['output']
                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    a_id = tokenizer.encode(a, add_special_tokens=False)
                    text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(q +  a + '\n')

    print('valid_medical: valid_encyclopedia')
    data_name = f'{data_path}/valid_encyclopedia.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                text = line['text']
                if tokenizer is not None:
                    text_id = tokenizer.encode(text, add_special_tokens=False)
                    text_id.append(tokenizer.special_tokens['<eos>'])
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(text + '\n')

    if len(doc_ids) > 0:
        arr = np.array(doc_ids, dtype=np.uint16)
        print(arr.shape)
        with open(f'{data_path}/valid_data.bin', 'wb') as f:
            f.write(arr.tobytes())

    if save_all_text:
        corpus_txts.close()

    print(f'processed process_valid_medical tokens: {total_id_len}')
    logger.info(f'processed process_valid_medical tokens: {total_id_len}')


def process_test_medical(tokenizer, save_all_text=False):
    data_path = GLOBAL_DATA_PATH
    if check_is_processed(f'{GLOBAL_DATA_PATH}/test_data.bin',data_path):
        print(f'test_data has been processed')
        return

    doc_ids = []
    total_id_len = 0

    if save_all_text:
        corpus_txts = open(f'./data/tokenizer_test_medical.txt', 'w', encoding='utf-8')

    print('test_medical: test_en_1')
    data_name = f'{data_path}/test_en_1.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['input']
                a = line['output']
                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    a_id = tokenizer.encode(a, add_special_tokens=False)
                    text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(q + a +'\n')

    print('test_medical: test_zh_0')
    data_name = f'{data_path}/test_zh_0.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['instruction'] + line['input']
                a = line['output']
                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    a_id = tokenizer.encode(a, add_special_tokens=False)
                    text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(q + a +'\n')

    print('test_medical: test_encyclopedia')
    data_name = f'{data_path}/test_encyclopedia.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/shibing624/medical')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            for row in tqdm(f):
                line = json.loads(row)
                q = line['instruction'] + line['input']
                a = line['output']
                if tokenizer is not None:
                    q_id = tokenizer.encode(q, add_special_tokens=False)
                    a_id = tokenizer.encode(a, add_special_tokens=False)
                    text_id = q_id + a_id + [tokenizer.special_tokens['<eos>']]
                    if len(text_id) > GLOBAL_MIN_LEN:
                        doc_ids += text_id
                        total_id_len += len(text_id)
                if save_all_text:
                    corpus_txts.write(q + a +'\n')

    if len(doc_ids) > 0:
        arr = np.array(doc_ids, dtype=np.uint16)
        print(arr.shape)
        with open(f'{data_path}/test_data.bin', 'wb') as f:
            f.write(arr.tobytes())

    if save_all_text:
        corpus_txts.close()

    print(f'processed process_test_medical tokens: {total_id_len}')
    logger.info(f'processed process_test_medical tokens: {total_id_len}')


def sft_process(save_all_text=False):
    data_path = GLOBAL_DATA_PATH
    if check_is_processed(f'{GLOBAL_DATA_PATH}/sft_data.csv',data_path):
        print(f'sft_data has been processed')
        return

    if save_all_text:
        corpus_txts = open(f'./data/tokenizer_sft_alpaca_gpt4_data_zh.txt', 'w', encoding='utf-8')

    data_name = f'{data_path}/alpaca_gpt4_data_zh.json'
    if not os.path.exists(data_name):
        print(
            f'{data_name} is not exist. please download from: https://huggingface.co/datasets/c-s-ale/alpaca-gpt4-data-zh')
    else:
        with open(data_name, 'r', encoding='utf-8') as f:
            data = json.load(f)

        q_lst = []
        a_lst = []
        for per in tqdm(data):
            q = per['instruction'] + per['input']
            a = per['output']
            if len(q) < 10 or len(a) < 5 or len(q) > 256 or len(a) > 256:
                continue
            q_lst.append(q)
            a_lst.append(a)

            if save_all_text:
                corpus_txts.write(q + a + '\n')


    data_name = f'{data_path}/Belle_open_source_1M.json'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/BelleGroup/train_1M_CN')
    else:
        f = open(data_name, 'r', encoding='utf-8')
        while True:
            line = f.readline()
            if not line:
                break
            per = json.loads(line)
            q = per['instruction'] + per['input']
            a = per['output']
            if len(q) < 10 or len(a) < 5 or len(q) > 256 or len(a) > 256:
                continue
            q_lst.append(q)
            a_lst.append(a)

            if save_all_text:
                corpus_txts.write(q + a + '\n')

    data_name = f'{data_path}/moss-003-sft-no-tools.jsonl'
    if not os.path.exists(data_name):
        print(f'{data_name} is not exist. please download from: https://huggingface.co/datasets/fnlp/moss-003-sft-data')
    else:
        f = open(data_name, 'r', encoding='utf-8')
        while True:
            line = f.readline()
            if not line:
                break
            per = json.loads(line)
            q = per['instruction'] + per['input']
            a = per['output']
            if len(q) < 10 or len(a) < 5 or len(q) > 256 or len(a) > 256:
                continue
            q_lst.append(q)
            a_lst.append(a)

            if save_all_text:
                corpus_txts.write(q + a + '\n')

    df = pd.DataFrame(columns=['prompt', 'answer'])
    df['prompt'] = q_lst
    df['answer'] = a_lst
    df.to_csv('data/sft_data.csv', index=False)
    print(df)

    if save_all_text:
        corpus_txts.close()