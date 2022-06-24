#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Configuration
import os
import sys
rootpath = os.path.sep.join(os.path.dirname(os.path.abspath(__file__)).split(os.path.sep)[:-1])
sys.path.append(rootpath)

from news import NewsCorpus, NewsIO, NewsPath
newsio = NewsIO()
newspath = NewsPath()

import json
from tqdm import tqdm
from collections import defaultdict, Counter


# def build_counter(do_build_counter, **kwargs):
#     global fname_word_counter, fname_doc_counter

#     if do_build_counter:
#         corpus = kwargs.get('corpus', '')

#         word_counter = defaultdict(int)
#         doc_counter = defaultdict(int)
#         attribute_errors = []
#         for doc in corpus.iter():
#             try:
#                 for w in itertools.chain(*doc.nouns_stop):
#                         word_counter[w] += 1
#                 for w in set(itertools.chain(*doc.nouns_stop)):
#                     doc_counter[w] += 1
#             except AttributeError:
#                 attribute_errors.append(doc)

#         newsio.save(_object=word_counter, _type='model', fname_object=fname_word_counter, verbose=False)
#         newsio.save(_object=doc_counter, _type='model', fname_object=fname_doc_counter, verbose=False)

#         print(f'  | fdir : {newspath.fdir_model}')
#         print(f'  | fname_word_counter: {fname_word_counter}')
#         print(f'  | fname_doc_counter: {fname_doc_counter}')
#         print(F'  | errors: {len(attribute_errors):,}')

#     else:
#         word_counter = newsio.load(fname_object=fname_word_counter, _type='model', verbose=False)
#         doc_counter = newsio.load(fname_object=fname_doc_counter, _type='model', verbose=False)

#     return word_counter, doc_counter

# def build_tfidf(do_build_tfidf, **kwargs):
#     global fname_tfidf

#     if do_build_tfidf:
#         corpus = kwargs.get('corpus', '')
#         word_counter = kwargs.get('word_counter', '')
#         doc_counter = kwargs.get('doc_counter', '')

#         tfidf = defaultdict(dict)
#         for w in tqdm(word_counter.keys()):
#             word_tf = word_counter[w]
#             word_df = doc_counter[w]
#             word_idf = np.log(DOCN / (df+1))
#             word_tfidf = tf*idf

#             tfidf[w] = {
#                 'tf': word_tf,
#                 'df': word_df,
#                 'idf': word_idf,
#                 'tfidf': word_tfidf
#             }

#         newsio.save(_object=tfidf, _type='model', fname_object=fname_tfidf, verbose=False)

#     else:
#         tfidf = newsio.load(fname_object=fname_tfidf, _type='model', verbose=False)

#     return tfidf

def text_feature_first_order(corpus, fname_text_feature_first_order):
    text_feature_first = defaultdict(dict)
    for yearmonth, docs in corpus.iter_month():
        word_list = []
        for doc in docs:
            for sent in doc['nouns_stop']:
                for word in sent:
                    word_list.append(word)

        text_feature_first['doc_count'][yearmonth] = len(docs)
        text_feature_first['word_count'][yearmonth] = Counter(word_list)
        text_feature_first['word_count_norm'][yearmonth] = {w: c/len(docs) for w, c in Counter(word_list).items()}

    fpath_text_feature_first_order = os.path.sep.join((newspath.fdir_data, fname_text_feature_first_order))
    with open(fpath_text_feature_first_order, 'w', encoding='utf-8') as f:
        json.dump(text_feature_first, f)
                                                             
def word_count_diff(counter_now, counter_before):
    counter_diff = {}
    for word, count_now in counter_now.items():
        try:
            count_before = counter_before[word]
        except KeyError:
            count_before = 0

        counter_diff[word] = count_now - count_before
    return counter_diff

def word_count_ratio(counter_now, counter_before):
    counter_ratio = {}
    for word, count_now in counter_now.items():
        try:
            count_before = counter_before[word]
        except KeyError:
            count_before = 0.0001

        counter_ratio[word] = count_now - count_before
    return counter_ratio

def text_feature_second_order(corpus, fname_text_feature_first_order, fname_text_feature_second_order):
    yearmonth_list = sorted(corpus.yearmonth_list, reverse=False)

    fpath_text_feature_first_order = os.path.sep.join((newspath.fdir_data, fname_text_feature_first_order))
    fpath_text_feature_second_order = os.path.sep.join((newspath.fdir_data, fname_text_feature_second_order))

    with open(fpath_text_feature_first_order, 'r', encoding='utf-8') as f:
        text_feature_first = defaultdict(dict, json.load(f))

    for yearmonth in tqdm(yearmonth_list):
        text_feature_first['word_count_portion'][yearmonth] = {w: c/sum(text_feature_first['word_count'][yearmonth].values()) for w, c in text_feature_first['word_count'][yearmonth].items()}

    text_feature_second = defaultdict(dict)
    for idx in tqdm(range(1, len(yearmonth_list))):
        _before = yearmonth_list[idx-1]
        _now = yearmonth_list[idx]

        text_feature_second['doc_count_diff'][_now] = text_feature_first['doc_count'][_now] - text_feature_first['doc_count'][_before]
        text_feature_second['doc_count_ratio'][_now] = text_feature_first['doc_count'][_now] / text_feature_first['doc_count'][_before]
        text_feature_second['word_count_diff'][_now] = word_count_diff(text_feature_first['word_count'][_now], text_feature_first['word_count'][_before])
        text_feature_second['word_count_ratio'][_now] = word_count_ratio(text_feature_first['word_count'][_now], text_feature_first['word_count'][_before])
        text_feature_second['word_count_norm_diff'][_now] = word_count_diff(text_feature_first['word_count_norm'][_now], text_feature_first['word_count_norm'][_before])
        text_feature_second['word_count_norm_ratio'][_now] = word_count_ratio(text_feature_first['word_count_norm'][_now], text_feature_first['word_count_norm'][_before])
        text_feature_second['word_count_portion_diff'][_now] = word_count_diff(text_feature_first['word_count_portion'][_now], text_feature_first['word_count_portion'][_before])
        text_feature_second['word_count_portion_ratio'][_now] = word_count_ratio(text_feature_first['word_count_portion'][_now], text_feature_first['word_count_portion'][_before])

    fpath_text_feature_first_order = os.path.sep.join((newspath.fdir_data, fname_text_feature_first_order))
    with open(fpath_text_feature_first_order, 'w', encoding='utf-8') as f:
        json.dump(text_feature_first, f)

    fpath_text_feature_second_order = os.path.sep.join((newspath.fdir_data, fname_text_feature_second_order))
    with open(fpath_text_feature_second_order, 'w', encoding='utf-8') as f:
        json.dump(text_feature_second, f)

def load_text_feature():
    fpath_text_feature_first_order = os.path.sep.join((newspath.fdir_data, fname_text_feature_first_order))
    with open(fpath_text_feature_first_order, 'r', encoding='utf-8') as f:
        text_feature_first = json.load(f)

    fpath_text_feature_second_order = os.path.sep.join((newspath.fdir_data, fname_text_feature_second_order))
    with open(fpath_text_feature_second_order, 'r', encoding='utf-8') as f:
        text_feature_second = json.load(f)

    return text_feature_first, text_feature_second


# def topic_feature


if __name__ == '__main__':
    ## Filenames
    fname_text_feature_first_order = 'text_feature_first_order.json'
    fname_text_feature_second_order = 'text_feature_second_order.json'
    # fname_tfidf = 'tfidf.pk'
    # fname_word_counter = 'word_counter.pk'
    # fname_doc_counter = 'doc_counter.pk'

    ## Parameters
    DO_FIRST_ORDER = False
    DO_SECOND_ORDER = False
    # do_build_counter = True
    # do_build_tfidf = True

    ## Data import
    print('============================================================')
    print('--------------------------------------------------')
    print('Load corpus')

    corpus = NewsCorpus(fdir_corpus=os.path.sep.join((newspath.root, 'corpus_topic_filtered')),
                        start='200501',
                        end='201912')

    ## Process
    print('============================================================')
    print('Text feature engineering')
    print('--------------------------------------------------')
    print('First order')

    if DO_FIRST_ORDER:
        text_feature_first_order(corpus, fname_text_feature_first_order)
    else:
        pass

    print('--------------------------------------------------')
    print('Second order')

    if DO_SECOND_ORDER:
        text_feature_second_order(corpus, fname_text_feature_first_order, fname_text_feature_second_order)
    else:
        pass

    print('--------------------------------------------------')
    print('Evaluate text features')

    text_feature_first, text_feature_second = load_text_feature()

    word_set = []
    for yearmonth in tqdm(corpus.yearmonth_list):
        word_set.extend(text_feature_first['word_count'][yearmonth].values())

    print('# of individual words: {:,}'.format(len(word_set)))