import numpy as np
import pandas as pd

from pathlib import Path
from typing import *

# --
import torch
import torch.optim as optim

# --
from fastai import *
from fastai.vision import *
from fastai.text import *
from fastai.callbacks import *

# --
class Config(dict):
  def __init__(self, **kwargs):
    super().__init__(kwargs)
    for k, v in kwargs.items():
      setattr(self, k, v)

  def set(self, k, v):
    self[k] = v
    setattr(self, k, v)


# --
config = Config(
  testing=False,
  bert_model_name="bert-base-uncased",
  max_lr=3e-5,
  epochs=4,
  use_fp16=True,
  bs=32,
  discriminative=False,
  max_seq_len=256)


# --
from pytorch_pretrained_bert import BertTokenizer
bert_tok = BertTokenizer.from_pretrained(config.bert_model_name)

# -- [6]
def _join_texts(
  text: Collection[str], mark_fields: bool = False,
  sos_token: Optional[str] = BOS):
  if not isinstance(text, np.ndarray):
    texts = np.array(texts)
  if is1d(texts):
    texts = texts[:,None]
  df = pd.DataFrame({i:texts[:,i] for i in range(texts.shape[1])})
  text_col = f'{FLD} {1}' + df[0].astype(str) if mark_fields else df[0].astype(str)
  if sos_token is not None:
    text_col = f"{sos_token} " + text_col
  for i in range(1, len(df.columns)):
    text_col += (f' {FLD} {i + 1} ' if mark_fields else '') + df[i].astype(str)
  return text_col.values


# -- [7]
class FastAiBertTokenizer(BaseTokenizer):
  """Wrapper around BertTokenizer to be compatible with fast.ai"""
  def __init__(self, tokenizer: BertTokenizer, max_seq_len: int=128, **kwargs):
    self._pretrained_tokenizer = tokenizer
    self.max_seq_len = max_seq_len

  def __call__(self, *args, **kwargs):
    return self

  def tokenizer(self, t:str) -> List[str]:
    """Limits the maximum sequence length"""
    return ["[CLS]"] + self._pretrained_tokenizer.tokenize(t)[:self.max_seq_len - 2] + ["[SEP]"]

# -- [8]
from sklearn.model_selection import train_test_split

#DATA_ROOT = Path("..") / "input"
DATA_ROOT = Path("/data1/is/src/Practical_NLP_in_PyTorch/data/jigsaw")

train, test = [pd.read_csv(DATA_ROOT / fname) for fname in ["train.csv", "test.csv"]]
train, val = train_test_split(train)

# -- [9]
if config.testing:
    train = train.head(1024)
    val = val.head(1024)
    test = test.head(1024)

# -- [10]
fastai_bert_vocab = Vocab(list(bert_tok.vocab.keys()))


# -- [11]
fastai_tokenizer = Tokenizer(
  tok_func=FastAiBertTokenizer(bert_tok, max_seq_len=config.max_seq_len),
  pre_rules=[], post_rules=[])

# -- [12]
label_cols = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

# databunch = TextDataBunch.from_df(".", train, val, test,
#                   tokenizer=fastai_tokenizer,
#                   vocab=fastai_bert_vocab,
#                   include_bos=False,
#                   include_eos=False,
#                   text_cols="comment_text",
#                   label_cols=label_cols,
#                   bs=config.bs,
#                   collate_fn=partial(pad_collate, pad_first=False, pad_idx=0),
#              )

# -- [13]
class BertTokenizeProcessor(TokenizeProcessor):
    def __init__(self, tokenizer):
        super().__init__(tokenizer=tokenizer, include_bos=False, include_eos=False)

class BertNumericalizeProcessor(NumericalizeProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, vocab=Vocab(list(bert_tok.vocab.keys())), **kwargs)

def get_bert_processor(tokenizer:Tokenizer=None, vocab:Vocab=None):
    """
    Constructing preprocessors for BERT
    We remove sos/eos tokens since we add that ourselves in the tokenizer.
    We also use a custom vocabulary to match the numericalization with the original BERT model.
    """
    return [BertTokenizeProcessor(tokenizer=tokenizer),
            NumericalizeProcessor(vocab=vocab)]


# -- [14]
class BertDataBunch(TextDataBunch):
    @classmethod
    def from_df(cls, path:PathOrStr, train_df:DataFrame, valid_df:DataFrame, test_df:Optional[DataFrame]=None,
                tokenizer:Tokenizer=None, vocab:Vocab=None, classes:Collection[str]=None, text_cols:IntsOrStrs=1,
                label_cols:IntsOrStrs=0, label_delim:str=None, **kwargs) -> DataBunch:
        "Create a `TextDataBunch` from DataFrames."
        p_kwargs, kwargs = split_kwargs_by_func(kwargs, get_bert_processor)
        # use our custom processors while taking tokenizer and vocab as kwargs
        processor = get_bert_processor(tokenizer=tokenizer, vocab=vocab, **p_kwargs)
        if classes is None and is_listy(label_cols) and len(label_cols) > 1: classes = label_cols
        src = ItemLists(path, TextList.from_df(train_df, path, cols=text_cols, processor=processor),
                        TextList.from_df(valid_df, path, cols=text_cols, processor=processor))
        src = src.label_for_lm() if cls==TextLMDataBunch else src.label_from_df(cols=label_cols, classes=classes)
        if test_df is not None: src.add_test(TextList.from_df(test_df, path, cols=text_cols))
        return src.databunch(**kwargs)


# -- 15
# this will produce a virtually identical databunch to the code above
databunch = BertDataBunch.from_df(".", train, val, test,
                  tokenizer=fastai_tokenizer,
                  vocab=fastai_bert_vocab,
                  text_cols="comment_text",
                  label_cols=label_cols,
                  bs=config.bs,
                  collate_fn=partial(pad_collate, pad_first=False, pad_idx=0),
             )


# -- [16]
from pytorch_pretrained_bert.modeling import BertConfig, BertForSequenceClassification
bert_model = BertForSequenceClassification.from_pretrained(config.bert_model_name, num_labels=6)


# -- [17]
loss_func = nn.BCEWithLogitsLoss()

# -- [18]
from fastai.callbacks import *

learner = Learner(
    databunch, bert_model,
    loss_func=loss_func,
)
if config.use_fp16: learner = learner.to_fp16()


# -- [19]
learner.lr_find()


# -- [20]
# learner.recorder.plot()

# -- [21]
learner.fit_one_cycle(config.epochs, max_lr=config.max_lr)


# -- [22]
def get_preds_as_nparray(ds_type) -> np.ndarray:
    """
    the get_preds method does not yield the elements in order by default
    we borrow the code from the RNNLearner to resort the elements into their correct order
    """
    preds = learner.get_preds(ds_type)[0].detach().cpu().numpy()
    sampler = [i for i in databunch.dl(ds_type).sampler]
    reverse_sampler = np.argsort(sampler)
    return preds[reverse_sampler, :]


# -- [23]
test_preds = get_preds_as_nparray(DatasetType.Test)


# -- [24]
#sample_submission = pd.read_csv(DATA_ROOT / "sample_submission.csv")
#if config.testing: sample_submission = sample_submission.head(test.shape[0])
#sample_submission[label_cols] = test_preds
#sample_submission.to_csv("predictions.csv", index=False)
print(test_preds)

