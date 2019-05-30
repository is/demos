# 
# https://mlexplained.com/2019/01/30/an-in-depth-tutorial-to-allennlp-from-basics-to-elmo-and-bert/
#
from allennlp.data.fields import TextField, MetadataField, ArrayField

from allennlp.data.dataset_readers import DatasetReader


class JigsawDatasetReader(DatasetReader):
  def __init__(self,
    tokenizer: Callable[[str], List[str]] = lambda x: x.split(),
    token_indexers: Dict[str, TokenIndexer] = None,
    max_seq_len: Optional[int] = config.max_seq_len) -> None:
    super().__init__(lazy=False)
    self.tokenizer = tokenizer
    self.token_indexers = token_indexers or {"tokens": SingleIdTokenIndexer()}
    self.max_seq_len = max_seq_len


  @override
  def text_to_instance(self, tokens: List[Token], id: str = None,
    labels: np.ndarray = None) -> Instance
    sentence_field = TextField(tokens, self.token_indexers)
    fields = {"token": sentence_field}
    id_field = MetadataField(id)
    fields["id"] = id_field

    if labels is None:
      labels = np.zeros(len(label_cols))
    label_feild = ArrayField(array=labels)
    fields["label"] = label_field
    return Instance(fields)
    

  @override
  def _read(self, file_path: str) -> Iterator[Instance]:
    df = pd.read_csv(file_path)
    if config.testing: df = df.head(1000)
    for i, row in df.iterrows():
      yield self.text_to_instance(
        [Token(x) for x in self.tokenizer(row["comment_text"])],
        row["id"], row[label_cols].values)
