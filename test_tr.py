import pickle
import argparse
import numpy as np
import sklearn
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import BernoulliNB
from sklearn import tree
parser = argparse.ArgumentParser()
parser.add_argument("--alpha", type=float)
parser.add_argument("--bn", type=float)
parser.add_argument("--fp", type=bool)


def feature_encode_pickle_file(inp_file_name, out_file_name):
    with open(file=inp_file_name, mode="rb") as file:
        data = pickle.load(file)

    vectorizer = HashingVectorizer()
    all_word_list = [*data['x_train'], *data['x_test']]
    vectorizer.fit(all_word_list)
    data['x_train'] = vectorizer.transform(data['x_train'])
    data['x_test'] = vectorizer.transform(data['x_test'])

    with open(file=out_file_name, mode="wb") as f:
        pickle.dump(data, f)


def sklearn_part():


    inp_fn = "./data/scikit-learn-data.pickle"
    out_fn = "./data/scikit-learn-data_formated.pickle"

    # feature_encode_pickle_file(inp_fn, out_fn)
    with open(file=out_fn, mode="rb") as file:
        data = pickle.load(file)

    args = parser.parse_args()
    classifier = BernoulliNB(
        alpha=args.alpha,
        binarize=args.bn,
        fit_prior=args.fp,

    )
    classifier.fit(X=data["x_train"], y=data['y_train'])
    y_hat = classifier.predict(data['x_test'])

    score = accuracy_score(data['y_test'], y_hat)
    print()
    print("BernoulliNB")
    print(f"score: {score}")

    # classifier = tree.DecisionTreeClassifier(max_depth=10)
    # classifier.fit(X=data["x_train"], y=data['y_train'])
    # y_hat = classifier.predict(data['x_test'])
    #
    # score = accuracy_score(data['y_test'], y_hat)
    # print()
    # print("decission tree")
    # print(f"score: {score}")


def preprocess_nn_dat(dat,ml):
    return keras.preprocessing.sequence.pad_sequences(
        dat,
        maxlen=ml,
        dtype='int32',
        padding='pre',
        truncating='pre',
        value=0.0
    )

def main():
    sklearn_part()

if __name__ == '__main__':
    main()

