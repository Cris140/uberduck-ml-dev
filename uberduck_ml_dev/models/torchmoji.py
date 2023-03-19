# TODO (Sam): move to encoders
from __future__ import absolute_import, division, print_function, unicode_literals


from __future__ import print_function, division, unicode_literals


__all__ = [
    "SPECIAL_PREFIX",
    "SPECIAL_TOKENS",
    "NB_TOKENS",
    "NB_EMOJI_CLASSES",
    "FINETUNING_METHODS",
    "FINETUNING_METRICS",
    "ALLOWED_EMOJIS",
    "EMOJIS",
    "LSTMHardSigmoid",
    "AutogradRNN",
    "Recurrent",
    "variable_recurrent_factory",
    "VariableRecurrent",
    "VariableRecurrentReverse",
    "StackedRNN",
    "LSTMCell",
    "hard_sigmoid",
    "tokenize",
    "RE_NUM",
    "RE_WORD",
    "RE_WHITESPACE",
    "RE_ANY",
    "RE_COMB",
    "RE_CONTRACTIONS",
    "TITLES",
    "RE_TITLES",
    "SYMBOLS",
    "RE_SYMBOL",
    "SPECIAL_SYMBOLS",
    "RE_ABBREVIATIONS",
    "RE_HASHTAG",
    "RE_MENTION",
    "RE_URL",
    "RE_EMAIL",
    "RE_HEART",
    "EMOTICONS_START",
    "EMOTICONS_MID",
    "EMOTICONS_END",
    "EMOTICONS_EXTRA",
    "RE_EMOTICON",
    "RE_EMOJI",
    "TOKENS",
    "IGNORED",
    "RE_PATTERN",
    "TorchmojiAttention",
    "VocabBuilder",
    "MasterVocab",
    "all_words_in_sentences",
    "extend_vocab_in_file",
    "extend_vocab",
    "SentenceTokenizer",
    "coverage",
    "torchmoji_feature_encoding",
    "torchmoji_emojis",
    "torchmoji_transfer",
    "TorchMoji",
    "load_specific_weights",
    "load_benchmark",
    "calculate_batchsize_maxlen",
    "freeze_layers",
    "change_trainable",
    "find_f1_threshold",
    "finetune",
    "tune_trainable",
    "evaluate_using_weighted_f1",
    "evaluate_using_acc",
    "chain_thaw",
    "train_by_chain_thaw",
    "calc_loss",
    "fit_model",
    "get_data_loader",
    "DeepMojiDataset",
    "DeepMojiBatchSampler",
    "relabel",
    "class_avg_finetune",
    "prepare_labels",
    "prepare_generators",
    "class_avg_tune_trainable",
    "class_avg_chainthaw",
    "read_english",
    "read_wanted_emojis",
    "read_non_english_users",
    "is_special_token",
    "mostly_english",
    "correct_length",
    "punct_word",
    "load_non_english_user_set",
    "non_english_user",
    "separate_emojis_and_text",
    "extract_emojis",
    "remove_variation_selectors",
    "shorten_word",
    "detect_special_tokens",
    "process_word",
    "remove_control_chars",
    "convert_nonbreaking_space",
    "convert_linebreaks",
    "AtMentionRegex",
    "urlRegex",
    "VARIATION_SELECTORS",
    "ALL_CHARS",
    "CONTROL_CHARS",
    "CONTROL_CHAR_REGEX",
    "WordGenerator",
    "TweetWordGenerator",
    "RETWEETS_RE",
    "URLS_RE",
    "MENTION_RE",
    "ALLOWED_CONVERTED_UNICODE_PUNCTUATION",
    "TorchMojiInterface",
]


# nbdev_comment from __future__ import absolute_import, division, print_function, unicode_literals

import re
import math
import torch
import glob
import json
import uuid
import codecs
import csv
from copy import deepcopy
from collections import defaultdict, OrderedDict
from itertools import groupby
import numpy as np
import pickle
from time import sleep
import unicodedata
from text_unidecode import unidecode
import string
import sys
from os.path import abspath, dirname, exists

from io import open

from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
import emoji

import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn.parameter import Parameter
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence, PackedSequence
from torch.autograd import Variable
import torch.nn.functional as F
from torch.autograd import Variable
from torch.utils.data import Dataset, DataLoader
from torch.utils.data.sampler import BatchSampler, SequentialSampler
from torch.nn.utils import clip_grad_norm


# torchmoji/global_variables.py

""" Global variables.
"""

# The ordering of these special tokens matter
# blank tokens can be used for new purposes
# Tokenizer should be updated if special token prefix is changed
SPECIAL_PREFIX = "CUSTOM_"
SPECIAL_TOKENS = [
    "CUSTOM_MASK",
    "CUSTOM_UNKNOWN",
    "CUSTOM_AT",
    "CUSTOM_URL",
    "CUSTOM_NUMBER",
    "CUSTOM_BREAK",
]
SPECIAL_TOKENS.extend([f"{SPECIAL_PREFIX}BLANK_{i}" for i in range(6, 10)])

NB_TOKENS = 50000
NB_EMOJI_CLASSES = 64
FINETUNING_METHODS = ["last", "full", "new", "chain-thaw"]
FINETUNING_METRICS = ["acc", "weighted"]

ALLOWED_EMOJIS = emoji.get_emoji_unicode_dict("en").values()

# Emoji map in emoji_overview.png
EMOJIS = ":joy: :unamused: :weary: :sob: :heart_eyes: \
:pensive: :ok_hand: :blush: :heart: :smirk: \
:grin: :notes: :flushed: :100: :sleeping: \
:relieved: :relaxed: :raised_hands: :two_hearts: :expressionless: \
:sweat_smile: :pray: :confused: :kissing_heart: :heartbeat: \
:neutral_face: :information_desk_person: :disappointed: :see_no_evil: :tired_face: \
:v: :sunglasses: :rage: :thumbsup: :cry: \
:sleepy: :yum: :triumph: :hand: :mask: \
:clap: :eyes: :gun: :persevere: :smiling_imp: \
:sweat: :broken_heart: :yellow_heart: :musical_note: :speak_no_evil: \
:wink: :skull: :confounded: :smile: :stuck_out_tongue_winking_eye: \
:angry: :no_good: :muscle: :facepunch: :purple_heart: \
:sparkling_heart: :blue_heart: :grimacing: :sparkles:".split(
    " "
)


# torchmoji/lstm.py

""" Implement a pyTorch LSTM with hard sigmoid reccurent activation functions.
    Adapted from the non-cuda variant of pyTorch LSTM at
    https://github.com/pytorch/pytorch/blob/master/torch/nn/_functions/rnn.py
"""


class LSTMHardSigmoid(nn.Module):
    def __init__(
        self,
        input_size,
        hidden_size,
        num_layers=1,
        bias=True,
        batch_first=False,
        dropout=0,
        bidirectional=False,
    ):
        super(LSTMHardSigmoid, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bias = bias
        self.batch_first = batch_first
        self.dropout = dropout
        self.dropout_state = {}
        self.bidirectional = bidirectional
        num_directions = 2 if bidirectional else 1

        gate_size = 4 * hidden_size

        self._all_weights = []
        for layer in range(num_layers):
            for direction in range(num_directions):
                layer_input_size = (
                    input_size if layer == 0 else hidden_size * num_directions
                )

                w_ih = Parameter(torch.Tensor(gate_size, layer_input_size))
                w_hh = Parameter(torch.Tensor(gate_size, hidden_size))
                b_ih = Parameter(torch.Tensor(gate_size))
                b_hh = Parameter(torch.Tensor(gate_size))
                layer_params = (w_ih, w_hh, b_ih, b_hh)

                suffix = "_reverse" if direction == 1 else ""
                param_names = ["weight_ih_l{}{}", "weight_hh_l{}{}"]
                if bias:
                    param_names += ["bias_ih_l{}{}", "bias_hh_l{}{}"]
                param_names = [x.format(layer, suffix) for x in param_names]

                for name, param in zip(param_names, layer_params):
                    setattr(self, name, param)
                self._all_weights.append(param_names)

        self.flatten_parameters()
        self.reset_parameters()

    def flatten_parameters(self):
        """Resets parameter data pointer so that they can use faster code paths.

        Right now, this is a no-op wince we don't use CUDA acceleration.
        """
        self._data_ptrs = []

    def _apply(self, fn):
        ret = super(LSTMHardSigmoid, self)._apply(fn)
        self.flatten_parameters()
        return ret

    def reset_parameters(self):
        stdv = 1.0 / math.sqrt(self.hidden_size)
        for weight in self.parameters():
            weight.data.uniform_(-stdv, stdv)

    def forward(self, input, hx=None):
        is_packed = isinstance(input, PackedSequence)
        if is_packed:
            input, batch_sizes, _, _ = input
            max_batch_size = batch_sizes[0]
        else:
            batch_sizes = None
            max_batch_size = input.size(0) if self.batch_first else input.size(1)

        if hx is None:
            num_directions = 2 if self.bidirectional else 1
            hx = torch.autograd.Variable(
                input.data.new(
                    self.num_layers * num_directions, max_batch_size, self.hidden_size
                ).zero_(),
                requires_grad=False,
            )
            hx = (hx, hx)

        has_flat_weights = (
            list(p.data.data_ptr() for p in self.parameters()) == self._data_ptrs
        )
        if has_flat_weights:
            first_data = next(self.parameters()).data
            assert first_data.storage().size() == self._param_buf_size
            flat_weight = first_data.new().set_(
                first_data.storage(), 0, torch.Size([self._param_buf_size])
            )
        else:
            flat_weight = None
        func = AutogradRNN(
            self.input_size,
            self.hidden_size,
            num_layers=self.num_layers,
            batch_first=self.batch_first,
            dropout=self.dropout,
            train=self.training,
            bidirectional=self.bidirectional,
            batch_sizes=batch_sizes,
            dropout_state=self.dropout_state,
            flat_weight=flat_weight,
        )
        output, hidden = func(input, self.all_weights, hx)
        if is_packed:
            output = PackedSequence(output, batch_sizes)
        return output, hidden

    def __repr__(self):
        s = "{name}({input_size}, {hidden_size}"
        if self.num_layers != 1:
            s += ", num_layers={num_layers}"
        if self.bias is not True:
            s += ", bias={bias}"
        if self.batch_first is not False:
            s += ", batch_first={batch_first}"
        if self.dropout != 0:
            s += ", dropout={dropout}"
        if self.bidirectional is not False:
            s += ", bidirectional={bidirectional}"
        s += ")"
        return s.format(name=self.__class__.__name__, **self.__dict__)

    def __setstate__(self, d):
        super(LSTMHardSigmoid, self).__setstate__(d)
        self.__dict__.setdefault("_data_ptrs", [])
        if "all_weights" in d:
            self._all_weights = d["all_weights"]
        if isinstance(self._all_weights[0][0], str):
            return
        num_layers = self.num_layers
        num_directions = 2 if self.bidirectional else 1
        self._all_weights = []
        for layer in range(num_layers):
            for direction in range(num_directions):
                suffix = "_reverse" if direction == 1 else ""
                weights = [
                    "weight_ih_l{}{}",
                    "weight_hh_l{}{}",
                    "bias_ih_l{}{}",
                    "bias_hh_l{}{}",
                ]
                weights = [x.format(layer, suffix) for x in weights]
                if self.bias:
                    self._all_weights += [weights]
                else:
                    self._all_weights += [weights[:2]]

    @property
    def all_weights(self):
        return [
            [getattr(self, weight) for weight in weights]
            for weights in self._all_weights
        ]


def AutogradRNN(
    input_size,
    hidden_size,
    num_layers=1,
    batch_first=False,
    dropout=0,
    train=True,
    bidirectional=False,
    batch_sizes=None,
    dropout_state=None,
    flat_weight=None,
):

    cell = LSTMCell

    if batch_sizes is None:
        rec_factory = Recurrent
    else:
        rec_factory = variable_recurrent_factory(batch_sizes)

    if bidirectional:
        layer = (rec_factory(cell), rec_factory(cell, reverse=True))
    else:
        layer = (rec_factory(cell),)

    func = StackedRNN(layer, num_layers, True, dropout=dropout, train=train)

    def forward(input, weight, hidden):
        if batch_first and batch_sizes is None:
            input = input.transpose(0, 1)

        nexth, output = func(input, hidden, weight)

        if batch_first and batch_sizes is None:
            output = output.transpose(0, 1)

        return output, nexth

    return forward


def Recurrent(inner, reverse=False):
    def forward(input, hidden, weight):
        output = []
        steps = range(input.size(0) - 1, -1, -1) if reverse else range(input.size(0))
        for i in steps:
            hidden = inner(input[i], hidden, *weight)
            # hack to handle LSTM
            output.append(hidden[0] if isinstance(hidden, tuple) else hidden)

        if reverse:
            output.reverse()
        output = torch.cat(output, 0).view(input.size(0), *output[0].size())

        return hidden, output

    return forward


def variable_recurrent_factory(batch_sizes):
    def fac(inner, reverse=False):
        if reverse:
            return VariableRecurrentReverse(batch_sizes, inner)
        else:
            return VariableRecurrent(batch_sizes, inner)

    return fac


def VariableRecurrent(batch_sizes, inner):
    def forward(input, hidden, weight):
        output = []
        input_offset = 0
        last_batch_size = batch_sizes[0]
        hiddens = []
        flat_hidden = not isinstance(hidden, tuple)
        if flat_hidden:
            hidden = (hidden,)
        for batch_size in batch_sizes:
            step_input = input[input_offset : input_offset + batch_size]
            input_offset += batch_size

            dec = last_batch_size - batch_size
            if dec > 0:
                hiddens.append(tuple(h[-dec:] for h in hidden))
                hidden = tuple(h[:-dec] for h in hidden)
            last_batch_size = batch_size

            if flat_hidden:
                hidden = (inner(step_input, hidden[0], *weight),)
            else:
                hidden = inner(step_input, hidden, *weight)

            output.append(hidden[0])
        hiddens.append(hidden)
        hiddens.reverse()

        hidden = tuple(torch.cat(h, 0) for h in zip(*hiddens))
        assert hidden[0].size(0) == batch_sizes[0]
        if flat_hidden:
            hidden = hidden[0]
        output = torch.cat(output, 0)

        return hidden, output

    return forward


def VariableRecurrentReverse(batch_sizes, inner):
    def forward(input, hidden, weight):
        output = []
        input_offset = input.size(0)
        last_batch_size = batch_sizes[-1]
        initial_hidden = hidden
        flat_hidden = not isinstance(hidden, tuple)
        if flat_hidden:
            hidden = (hidden,)
            initial_hidden = (initial_hidden,)
        hidden = tuple(h[: batch_sizes[-1]] for h in hidden)
        for batch_size in reversed(batch_sizes):
            inc = batch_size - last_batch_size
            if inc > 0:
                hidden = tuple(
                    torch.cat((h, ih[last_batch_size:batch_size]), 0)
                    for h, ih in zip(hidden, initial_hidden)
                )
            last_batch_size = batch_size
            step_input = input[input_offset - batch_size : input_offset]
            input_offset -= batch_size

            if flat_hidden:
                hidden = (inner(step_input, hidden[0], *weight),)
            else:
                hidden = inner(step_input, hidden, *weight)
            output.append(hidden[0])

        output.reverse()
        output = torch.cat(output, 0)
        if flat_hidden:
            hidden = hidden[0]
        return hidden, output

    return forward


def StackedRNN(inners, num_layers, lstm=False, dropout=0, train=True):

    num_directions = len(inners)
    total_layers = num_layers * num_directions

    def forward(input, hidden, weight):
        assert len(weight) == total_layers
        next_hidden = []

        if lstm:
            hidden = list(zip(*hidden))

        for i in range(num_layers):
            all_output = []
            for j, inner in enumerate(inners):
                l = i * num_directions + j

                hy, output = inner(input, hidden[l], weight[l])
                next_hidden.append(hy)
                all_output.append(output)

            input = torch.cat(all_output, input.dim() - 1)

            if dropout != 0 and i < num_layers - 1:
                input = F.dropout(input, p=dropout, training=train, inplace=False)

        if lstm:
            next_h, next_c = zip(*next_hidden)
            next_hidden = (
                torch.cat(next_h, 0).view(total_layers, *next_h[0].size()),
                torch.cat(next_c, 0).view(total_layers, *next_c[0].size()),
            )
        else:
            next_hidden = torch.cat(next_hidden, 0).view(
                total_layers, *next_hidden[0].size()
            )

        return next_hidden, input

    return forward


def LSTMCell(input, hidden, w_ih, w_hh, b_ih=None, b_hh=None):
    """
    A modified LSTM cell with hard sigmoid activation on the input, forget and output gates.
    """
    hx, cx = hidden
    gates = F.linear(input, w_ih, b_ih) + F.linear(hx, w_hh, b_hh)

    ingate, forgetgate, cellgate, outgate = gates.chunk(4, 1)

    ingate = hard_sigmoid(ingate)
    forgetgate = hard_sigmoid(forgetgate)
    cellgate = F.tanh(cellgate)
    outgate = hard_sigmoid(outgate)

    cy = (forgetgate * cx) + (ingate * cellgate)
    hy = outgate * F.tanh(cy)

    return hy, cy


def hard_sigmoid(x):
    """
    Computes element-wise hard sigmoid of x.
    See e.g. https://github.com/Theano/Theano/blob/master/theano/tensor/nnet/sigm.py#L279
    """
    x = (0.2 * x) + 0.5
    x = F.threshold(-x, -1, -1)
    x = F.threshold(-x, 0, 0)
    return x


# torchmoji/tokenizer.py

"""
Splits up a Unicode string into a list of tokens.
Recognises:
- Abbreviations
- URLs
- Emails
- #hashtags
- @mentions
- emojis
- emoticons (limited support)

Multiple consecutive symbols are also treated as a single token.
"""


# Basic patterns.
RE_NUM = r"[0-9]+"
RE_WORD = r"[a-zA-Z]+"
RE_WHITESPACE = r"\s+"
RE_ANY = r"."

# Combined words such as 'red-haired' or 'CUSTOM_TOKEN'
RE_COMB = r"[a-zA-Z]+[-_][a-zA-Z]+"

# English-specific patterns
RE_CONTRACTIONS = RE_WORD + r"\'" + RE_WORD

TITLES = [
    r"Mr\.",
    r"Ms\.",
    r"Mrs\.",
    r"Dr\.",
    r"Prof\.",
]
# Ensure case insensitivity
RE_TITLES = r"|".join([r"(?i)" + t for t in TITLES])

# Symbols have to be created as separate patterns in order to match consecutive
# identical symbols.
SYMBOLS = r"()<!?.,/\'\"-_=\\§|´ˇ°[]<>{}~$^&*;:%+\xa3€`"
RE_SYMBOL = r"|".join([re.escape(s) + r"+" for s in SYMBOLS])

# Hash symbols and at symbols have to be defined separately in order to not
# clash with hashtags and mentions if there are multiple - i.e.
# ##hello -> ['#', '#hello'] instead of ['##', 'hello']
SPECIAL_SYMBOLS = r"|#+(?=#[a-zA-Z0-9_]+)|@+(?=@[a-zA-Z0-9_]+)|#+|@+"
RE_SYMBOL += SPECIAL_SYMBOLS

RE_ABBREVIATIONS = r"\b(?<!\.)(?:[A-Za-z]\.){2,}"

# Twitter-specific patterns
RE_HASHTAG = r"#[a-zA-Z0-9_]+"
RE_MENTION = r"@[a-zA-Z0-9_]+"

RE_URL = r"(?:https?://|www\.)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
RE_EMAIL = r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"

# Emoticons and emojis
RE_HEART = r"(?:<+/?3+)+"
EMOTICONS_START = [
    r">:",
    r":",
    r"=",
    r";",
]
EMOTICONS_MID = [
    r"-",
    r",",
    r"^",
    "'",
    '"',
]
EMOTICONS_END = [
    r"D",
    r"d",
    r"p",
    r"P",
    r"v",
    r")",
    r"o",
    r"O",
    r"(",
    r"3",
    r"/",
    r"|",
    "\\",
]
EMOTICONS_EXTRA = [
    r"-_-",
    r"x_x",
    r"^_^",
    r"o.o",
    r"o_o",
    r"(:",
    r"):",
    r");",
    r"(;",
]

RE_EMOTICON = r"|".join([re.escape(s) for s in EMOTICONS_EXTRA])
for s in EMOTICONS_START:
    for m in EMOTICONS_MID:
        for e in EMOTICONS_END:
            RE_EMOTICON += "|{0}{1}?{2}+".format(
                re.escape(s), re.escape(m), re.escape(e)
            )

# requires ucs4 in python2.7 or python3+
# RE_EMOJI = r"""[\U0001F300-\U0001F64F\U0001F680-\U0001F6FF\u2600-\u26FF\u2700-\u27BF]"""
# safe for all python
RE_EMOJI = r"""\ud83c[\udf00-\udfff]|\ud83d[\udc00-\ude4f\ude80-\udeff]|[\u2600-\u26FF\u2700-\u27BF]"""

# List of matched token patterns, ordered from most specific to least specific.
TOKENS = [
    RE_URL,
    RE_EMAIL,
    RE_COMB,
    RE_HASHTAG,
    RE_MENTION,
    RE_HEART,
    RE_EMOTICON,
    RE_CONTRACTIONS,
    RE_TITLES,
    RE_ABBREVIATIONS,
    RE_NUM,
    RE_WORD,
    RE_SYMBOL,
    RE_EMOJI,
    RE_ANY,
]

# List of ignored token patterns
IGNORED = [RE_WHITESPACE]

# Final pattern
RE_PATTERN = re.compile(
    r"|".join(IGNORED) + r"|(" + r"|".join(TOKENS) + r")", re.UNICODE
)


def tokenize(text):
    """Splits given input string into a list of tokens.

    # Arguments:
        text: Input string to be tokenized.

    # Returns:
        List of strings (tokens).
    """
    result = RE_PATTERN.findall(text)

    # Remove empty strings
    result = [t for t in result if t.strip()]
    return result


# torchmoji/attlayer.py

""" Define the Attention Layer of the model.
"""


class TorchmojiAttention(nn.Module):
    """
    Computes a weighted average of the different channels across timesteps.
    Uses 1 parameter pr. channel to compute the attention value for a single timestep.
    """

    def __init__(self, attention_size, return_attention=False):
        """Initialize the attention layer

        # Arguments:
            attention_size: Size of the attention vector.
            return_attention: If true, output will include the weight for each input token
                              used for the prediction

        """
        super(TorchmojiAttention, self).__init__()
        self.return_attention = return_attention
        self.attention_size = attention_size
        self.attention_vector = Parameter(torch.FloatTensor(attention_size))
        self.attention_vector.data.normal_(std=0.05)  # Initialize attention vector

    def __repr__(self):
        s = "{name}({attention_size}, return attention={return_attention})"
        return s.format(name=self.__class__.__name__, **self.__dict__)

    def forward(self, inputs, input_lengths):
        """Forward pass.

        # Arguments:
            inputs (Torch.Variable): Tensor of input sequences
            input_lengths (torch.LongTensor): Lengths of the sequences

        # Return:
            Tuple with (representations and attentions if self.return_attention else None).
        """
        logits = inputs.matmul(self.attention_vector)
        unnorm_ai = (logits - logits.max()).exp()

        # Compute a mask for the attention on the padded sequences
        # See e.g. https://discuss.pytorch.org/t/self-attention-on-words-and-masking/5671/5
        max_len = unnorm_ai.size(1)
        idxes = torch.arange(0, max_len, out=torch.LongTensor(max_len)).unsqueeze(0)
        #         if torch.cuda.is_available():
        #             idxes = idxes.cuda()

        mask = Variable((idxes < input_lengths.unsqueeze(1)).float())

        # apply mask and renormalize attention scores (weights)
        masked_weights = unnorm_ai * mask
        att_sums = masked_weights.sum(dim=1, keepdim=True)  # sums per sequence
        attentions = masked_weights.div(att_sums)

        # apply attention weights
        weighted = torch.mul(inputs, attentions.unsqueeze(-1).expand_as(inputs))

        # get the final fixed vector representations of the sentences
        representations = weighted.sum(dim=1)

        return (representations, attentions if self.return_attention else None)


# torchmoji/create_vocab.py


class VocabBuilder:
    """Create vocabulary with words extracted from sentences as fed from a
    word generator.
    """

    def __init__(self, word_gen):
        # initialize any new key with value of 0
        self.word_counts = defaultdict(lambda: 0, {})
        self.word_length_limit = 30

        for token in SPECIAL_TOKENS:
            assert len(token) < self.word_length_limit
            self.word_counts[token] = 0
        self.word_gen = word_gen

    def count_words_in_sentence(self, words):
        """Generates word counts for all tokens in the given sentence.

        # Arguments:
            words: Tokenized sentence whose words should be counted.
        """
        for word in words:
            if 0 < len(word) and len(word) <= self.word_length_limit:
                try:
                    self.word_counts[word] += 1
                except KeyError:
                    self.word_counts[word] = 1

    def save_vocab(self, path=None):
        """Saves the vocabulary into a file.

        # Arguments:
            path: Where the vocabulary should be saved. If not specified, a
                  randomly generated filename is used instead.
        """
        dtype = [("word", "|S{}".format(self.word_length_limit)), ("count", "int")]
        np_dict = np.array(self.word_counts.items(), dtype=dtype)

        # sort from highest to lowest frequency
        np_dict[::-1].sort(order="count")
        data = np_dict

        if path is None:
            path = str(uuid.uuid4())

        np.savez_compressed(path, data=data)
        print("Saved dict to {}".format(path))

    def get_next_word(self):
        """Returns next tokenized sentence from the word geneerator.

        # Returns:
            List of strings, representing the next tokenized sentence.
        """
        return self.word_gen.__iter__().next()

    def count_all_words(self):
        """Generates word counts for all words in all sentences of the word
        generator.
        """
        for words, _ in self.word_gen:
            self.count_words_in_sentence(words)


class MasterVocab:
    """Combines vocabularies."""

    def __init__(self):

        # initialize custom tokens
        self.master_vocab = {}

    def populate_master_vocab(self, vocab_path, min_words=1, force_appearance=None):
        """Populates the master vocabulary using all vocabularies found in the
            given path. Vocabularies should be named *.npz. Expects the
            vocabularies to be numpy arrays with counts. Normalizes the counts
            and combines them.

        # Arguments:
            vocab_path: Path containing vocabularies to be combined.
            min_words: Minimum amount of occurences a word must have in order
                to be included in the master vocabulary.
            force_appearance: Optional vocabulary filename that will be added
                to the master vocabulary no matter what. This vocabulary must
                be present in vocab_path.
        """

        paths = glob.glob(vocab_path + "*.npz")
        sizes = {path: 0 for path in paths}
        dicts = {path: {} for path in paths}

        # set up and get sizes of individual dictionaries
        for path in paths:
            np_data = np.load(path)["data"]

            for entry in np_data:
                word, count = entry
                if count < min_words:
                    continue
                if is_special_token(word):
                    continue
                dicts[path][word] = count

            sizes[path] = sum(dicts[path].values())
            print("Overall word count for {} -> {}".format(path, sizes[path]))
            print("Overall word number for {} -> {}".format(path, len(dicts[path])))

        vocab_of_max_size = max(sizes, key=sizes.get)
        max_size = sizes[vocab_of_max_size]
        print("Min: {}, {}, {}".format(sizes, vocab_of_max_size, max_size))

        # can force one vocabulary to always be present
        if force_appearance is not None:
            force_appearance_path = [p for p in paths if force_appearance in p][0]
            force_appearance_vocab = deepcopy(dicts[force_appearance_path])
            print(force_appearance_path)
        else:
            force_appearance_path, force_appearance_vocab = None, None

        # normalize word counts before inserting into master dict
        for path in paths:
            normalization_factor = max_size / sizes[path]
            print("Norm factor for path {} -> {}".format(path, normalization_factor))

            for word in dicts[path]:
                if is_special_token(word):
                    print("SPECIAL - ", word)
                    continue
                normalized_count = dicts[path][word] * normalization_factor

                # can force one vocabulary to always be present
                if force_appearance_vocab is not None:
                    try:
                        force_word_count = force_appearance_vocab[word]
                    except KeyError:
                        continue
                    # if force_word_count < 5:
                    # continue

                if word in self.master_vocab:
                    self.master_vocab[word] += normalized_count
                else:
                    self.master_vocab[word] = normalized_count

        print("Size of master_dict {}".format(len(self.master_vocab)))
        print(
            "Hashes for master dict: {}".format(
                len([w for w in self.master_vocab if "#" in w[0]])
            )
        )

    def save_vocab(self, path_count, path_vocab, word_limit=100000):
        """Saves the master vocabulary into a file."""

        # reserve space for 10 special tokens
        words = OrderedDict()
        for token in SPECIAL_TOKENS:
            # store -1 instead of np.inf, which can overflow
            words[token] = -1

        # sort words by frequency
        desc_order = OrderedDict(
            sorted(self.master_vocab.items(), key=lambda kv: kv[1], reverse=True)
        )
        words.update(desc_order)

        # use encoding of up to 30 characters (no token conversions)
        # use float to store large numbers (we don't care about precision loss)
        np_vocab = np.array(
            words.items(), dtype=([("word", "|S30"), ("count", "float")])
        )

        # output count for debugging
        counts = np_vocab[:word_limit]
        np.savez_compressed(path_count, counts=counts)

        # output the index of each word for easy lookup
        final_words = OrderedDict()
        for i, w in enumerate(words.keys()[:word_limit]):
            final_words.update({w: i})
        with open(path_vocab, "w") as f:
            f.write(json.dumps(final_words, indent=4, separators=(",", ": ")))


def all_words_in_sentences(sentences):
    """Extracts all unique words from a given list of sentences.

    # Arguments:
        sentences: List or word generator of sentences to be processed.

    # Returns:
        List of all unique words contained in the given sentences.
    """
    vocab = []
    if isinstance(sentences, WordGenerator):
        sentences = [s for s, _ in sentences]

    for sentence in sentences:
        for word in sentence:
            if word not in vocab:
                vocab.append(word)

    return vocab


def extend_vocab_in_file(
    vocab, max_tokens=10000, vocab_path="../models/vocabulary.json"
):
    """Extends JSON-formatted vocabulary with words from vocab that are not
        present in the current vocabulary. Adds up to max_tokens words.
        Overwrites file in vocab_path.

    # Arguments:
        new_vocab: Vocabulary to be added. MUST have word_counts populated, i.e.
            must have run count_all_words() previously.
        max_tokens: Maximum number of words to be added.
        vocab_path: Path to the vocabulary json which is to be extended.
    """
    try:
        with open(vocab_path, "r") as f:
            current_vocab = json.load(f)
    except IOError:
        print("Vocabulary file not found, expected at " + vocab_path)
        return

    extend_vocab(current_vocab, vocab, max_tokens)

    # Save back to file
    with open(vocab_path, "w") as f:
        json.dump(current_vocab, f, sort_keys=True, indent=4, separators=(",", ": "))


def extend_vocab(current_vocab, new_vocab, max_tokens=10000):
    """Extends current vocabulary with words from vocab that are not
        present in the current vocabulary. Adds up to max_tokens words.

    # Arguments:
        current_vocab: Current dictionary of tokens.
        new_vocab: Vocabulary to be added. MUST have word_counts populated, i.e.
            must have run count_all_words() previously.
        max_tokens: Maximum number of words to be added.

    # Returns:
        How many new tokens have been added.
    """
    if max_tokens < 0:
        max_tokens = 10000

    words = OrderedDict()

    # sort words by frequency
    desc_order = OrderedDict(
        sorted(new_vocab.word_counts.items(), key=lambda kv: kv[1], reverse=True)
    )
    words.update(desc_order)

    base_index = len(current_vocab.keys())
    added = 0
    for word in words:
        if added >= max_tokens:
            break
        if word not in current_vocab.keys():
            current_vocab[word] = base_index + added
            added += 1

    return added


# torchmoji/sentence_tokenizer.py

"""
Provides functionality for converting a given list of tokens (words) into
numbers, according to the given vocabulary.
"""
# nbdev_comment from __future__ import print_function, division, unicode_literals

import numbers
import numpy as np

# import torch

from sklearn.model_selection import train_test_split

from copy import deepcopy


class SentenceTokenizer:
    """Create numpy array of tokens corresponding to input sentences.
    The vocabulary can include Unicode tokens.
    """

    def __init__(
        self,
        vocabulary,
        fixed_length,
        custom_wordgen=None,
        ignore_sentences_with_only_custom=False,
        masking_value=0,
        unknown_value=1,
    ):
        """Needs a dictionary as input for the vocabulary."""

        if len(vocabulary) > np.iinfo("uint16").max:
            raise ValueError(
                "Dictionary is too big ({} tokens) for the numpy "
                "datatypes used (max limit={}). Reduce vocabulary"
                " or adjust code accordingly!".format(
                    len(vocabulary), np.iinfo("uint16").max
                )
            )

        # Shouldn't be able to modify the given vocabulary
        self.vocabulary = deepcopy(vocabulary)
        self.fixed_length = fixed_length
        self.ignore_sentences_with_only_custom = ignore_sentences_with_only_custom
        self.masking_value = masking_value
        self.unknown_value = unknown_value

        # Initialized with an empty stream of sentences that must then be fed
        # to the generator at a later point for reusability.
        # A custom word generator can be used for domain-specific filtering etc
        if custom_wordgen is not None:
            assert custom_wordgen.stream is None
            self.wordgen = custom_wordgen
            self.uses_custom_wordgen = True
        else:
            self.wordgen = WordGenerator(
                None,
                allow_unicode_text=True,
                ignore_emojis=False,
                remove_variation_selectors=True,
                break_replacement=True,
            )
            self.uses_custom_wordgen = False

    def tokenize_sentences(self, sentences, reset_stats=True, max_sentences=None):
        """Converts a given list of sentences into a numpy array according to
            its vocabulary.

        # Arguments:
            sentences: List of sentences to be tokenized.
            reset_stats: Whether the word generator's stats should be reset.
            max_sentences: Maximum length of sentences. Must be set if the
                length cannot be inferred from the input.

        # Returns:
            Numpy array of the tokenization sentences with masking,
            infos,
            stats

        # Raises:
            ValueError: When maximum length is not set and cannot be inferred.
        """

        if max_sentences is None and not hasattr(sentences, "__len__"):
            raise ValueError(
                "Either you must provide an array with a length"
                "attribute (e.g. a list) or specify the maximum "
                "length yourself using `max_sentences`!"
            )
        n_sentences = max_sentences if max_sentences is not None else len(sentences)

        if self.masking_value == 0:
            tokens = np.zeros((n_sentences, self.fixed_length), dtype="uint16")
        else:
            tokens = (
                np.ones((n_sentences, self.fixed_length), dtype="uint16")
                * self.masking_value
            )

        if reset_stats:
            self.wordgen.reset_stats()

        # With a custom word generator info can be extracted from each
        # sentence (e.g. labels)
        infos = []

        # Returns words as strings and then map them to vocabulary
        self.wordgen.stream = sentences
        next_insert = 0
        n_ignored_unknowns = 0
        for s_words, s_info in self.wordgen:
            s_tokens = self.find_tokens(s_words)

            if self.ignore_sentences_with_only_custom and np.all(
                [True if t < len(SPECIAL_TOKENS) else False for t in s_tokens]
            ):
                n_ignored_unknowns += 1
                continue
            if len(s_tokens) > self.fixed_length:
                s_tokens = s_tokens[: self.fixed_length]
            tokens[next_insert, : len(s_tokens)] = s_tokens
            infos.append(s_info)
            next_insert += 1

        # For standard word generators all sentences should be tokenized
        # this is not necessarily the case for custom wordgenerators as they
        # may filter the sentences etc.
        if not self.uses_custom_wordgen and not self.ignore_sentences_with_only_custom:
            assert len(sentences) == next_insert
        else:
            # adjust based on actual tokens received
            tokens = tokens[:next_insert]
            infos = infos[:next_insert]

        return tokens, infos, self.wordgen.stats

    def find_tokens(self, words):
        assert len(words) > 0
        tokens = []
        for w in words:
            try:
                tokens.append(self.vocabulary[w])
            except KeyError:
                tokens.append(self.unknown_value)
        return tokens

    def split_train_val_test(
        self, sentences, info_dicts, split_parameter=[0.7, 0.1, 0.2], extend_with=0
    ):
        """Splits given sentences into three different datasets: training,
            validation and testing.

        # Arguments:
            sentences: The sentences to be tokenized.
            info_dicts: A list of dicts that contain information about each
                sentence (e.g. a label).
            split_parameter: A parameter for deciding the splits between the
                three different datasets. If instead of being passed three
                values, three lists are passed, then these will be used to
                specify which observation belong to which dataset.
            extend_with: An optional parameter. If > 0 then this is the number
                of tokens added to the vocabulary from this dataset. The
                expanded vocab will be generated using only the training set,
                but is applied to all three sets.

        # Returns:
            List of three lists of tokenized sentences,

            List of three corresponding dictionaries with information,

            How many tokens have been added to the vocab. Make sure to extend
            the embedding layer of the model accordingly.
        """

        # If passed three lists, use those directly
        if (
            isinstance(split_parameter, list)
            and all(isinstance(x, list) for x in split_parameter)
            and len(split_parameter) == 3
        ):

            # Helper function to verify provided indices are numbers in range
            def verify_indices(inds):
                return list(
                    filter(
                        lambda i: isinstance(i, numbers.Number) and i < len(sentences),
                        inds,
                    )
                )

            ind_train = verify_indices(split_parameter[0])
            ind_val = verify_indices(split_parameter[1])
            ind_test = verify_indices(split_parameter[2])
        else:
            # Split sentences and dicts
            ind = list(range(len(sentences)))
            ind_train, ind_test = train_test_split(ind, test_size=split_parameter[2])
            ind_train, ind_val = train_test_split(
                ind_train, test_size=split_parameter[1]
            )

        # Map indices to data
        train = np.array([sentences[x] for x in ind_train])
        test = np.array([sentences[x] for x in ind_test])
        val = np.array([sentences[x] for x in ind_val])

        info_train = np.array([info_dicts[x] for x in ind_train])
        info_test = np.array([info_dicts[x] for x in ind_test])
        info_val = np.array([info_dicts[x] for x in ind_val])

        added = 0
        # Extend vocabulary with training set tokens
        if extend_with > 0:
            wg = WordGenerator(train)
            vb = VocabBuilder(wg)
            vb.count_all_words()
            added = extend_vocab(self.vocabulary, vb, max_tokens=extend_with)

        # Wrap results
        result = [self.tokenize_sentences(s)[0] for s in [train, val, test]]
        result_infos = [info_train, info_val, info_test]
        # if type(result_infos[0][0]) in [np.double, np.float, np.int64, np.int32, np.uint8]:
        #     result_infos = [torch.from_numpy(label).long() for label in result_infos]

        return result, result_infos, added

    def to_sentence(self, sentence_idx):
        """Converts a tokenized sentence back to a list of words.

        # Arguments:
            sentence_idx: List of numbers, representing a tokenized sentence
                given the current vocabulary.

        # Returns:
            String created by converting all numbers back to words and joined
            together with spaces.
        """
        # Have to recalculate the mappings in case the vocab was extended.
        ind_to_word = {ind: word for word, ind in self.vocabulary.items()}

        sentence_as_list = [ind_to_word[x] for x in sentence_idx]
        cleaned_list = [x for x in sentence_as_list if x != "CUSTOM_MASK"]
        return " ".join(cleaned_list)


def coverage(dataset, verbose=False):
    """Computes the percentage of words in a given dataset that are unknown.

    # Arguments:
        dataset: Tokenized dataset to be checked.
        verbose: Verbosity flag.

    # Returns:
        Percentage of unknown tokens.
    """
    n_total = np.count_nonzero(dataset)
    n_unknown = np.sum(dataset == 1)
    coverage = 1.0 - float(n_unknown) / n_total

    if verbose:
        print("Unknown words: {}".format(n_unknown))
        print("Total words: {}".format(n_total))
        print("Coverage: {}".format(coverage))
    return coverage


# torchmoji/model_def.py
""" Model definition functions and weight loading.
"""


def torchmoji_feature_encoding(weight_path, return_attention=False, verbose=False):
    """Loads the pretrained torchMoji model for extracting features
        from the penultimate feature layer. In this way, it transforms
        the text into its emotional encoding.

    # Arguments:
        weight_path: Path to model weights to be loaded.
        return_attention: If true, output will include weight of each input token
            used for the prediction

    # Returns:
        Pretrained model for encoding text into feature vectors.
    """

    model = TorchMoji(
        nb_classes=None,
        nb_tokens=NB_TOKENS,
        feature_output=True,
        return_attention=return_attention,
    )
    load_specific_weights(
        model, weight_path, exclude_names=["output_layer"], verbose=verbose
    )
    return model


def torchmoji_emojis(weight_path, return_attention=False):
    """Loads the pretrained torchMoji model for extracting features
        from the penultimate feature layer. In this way, it transforms
        the text into its emotional encoding.

    # Arguments:
        weight_path: Path to model weights to be loaded.
        return_attention: If true, output will include weight of each input token
            used for the prediction

    # Returns:
        Pretrained model for encoding text into feature vectors.
    """

    model = TorchMoji(
        nb_classes=NB_EMOJI_CLASSES,
        nb_tokens=NB_TOKENS,
        return_attention=return_attention,
    )
    model.load_state_dict(torch.load(weight_path))
    return model


def torchmoji_transfer(
    nb_classes,
    weight_path=None,
    extend_embedding=0,
    embed_dropout_rate=0.1,
    final_dropout_rate=0.5,
):
    """Loads the pretrained torchMoji model for finetuning/transfer learning.
        Does not load weights for the softmax layer.

        Note that if you are planning to use class average F1 for evaluation,
        nb_classes should be set to 2 instead of the actual number of classes
        in the dataset, since binary classification will be performed on each
        class individually.

        Note that for the 'new' method, weight_path should be left as None.

    # Arguments:
        nb_classes: Number of classes in the dataset.
        weight_path: Path to model weights to be loaded.
        extend_embedding: Number of tokens that have been added to the
            vocabulary on top of NB_TOKENS. If this number is larger than 0,
            the embedding layer's dimensions are adjusted accordingly, with the
            additional weights being set to random values.
        embed_dropout_rate: Dropout rate for the embedding layer.
        final_dropout_rate: Dropout rate for the final Softmax layer.

    # Returns:
        Model with the given parameters.
    """

    model = TorchMoji(
        nb_classes=nb_classes,
        nb_tokens=NB_TOKENS + extend_embedding,
        embed_dropout_rate=embed_dropout_rate,
        final_dropout_rate=final_dropout_rate,
        output_logits=True,
    )
    if weight_path is not None:
        load_specific_weights(
            model,
            weight_path,
            exclude_names=["output_layer"],
            extend_embedding=extend_embedding,
        )
    return model


class TorchMoji(nn.Module):
    def __init__(
        self,
        nb_classes,
        nb_tokens,
        feature_output=False,
        output_logits=False,
        embed_dropout_rate=0,
        final_dropout_rate=0,
        return_attention=False,
    ):
        """
        torchMoji model.
        IMPORTANT: The model is loaded in evaluation mode by default (self.eval())

        # Arguments:
            nb_classes: Number of classes in the dataset.
            nb_tokens: Number of tokens in the dataset (i.e. vocabulary size).
            feature_output: If True the model returns the penultimate
                            feature vector rather than Softmax probabilities
                            (defaults to False).
            output_logits:  If True the model returns logits rather than probabilities
                            (defaults to False).
            embed_dropout_rate: Dropout rate for the embedding layer.
            final_dropout_rate: Dropout rate for the final Softmax layer.
            return_attention: If True the model also returns attention weights over the sentence
                              (defaults to False).
        """
        super(TorchMoji, self).__init__()

        embedding_dim = 256
        hidden_size = 512
        attention_size = 4 * hidden_size + embedding_dim

        self.feature_output = feature_output
        self.embed_dropout_rate = embed_dropout_rate
        self.final_dropout_rate = final_dropout_rate
        self.return_attention = return_attention
        self.hidden_size = hidden_size
        self.output_logits = output_logits
        self.nb_classes = nb_classes

        self.add_module("embed", nn.Embedding(nb_tokens, embedding_dim))
        # dropout2D: embedding channels are dropped out instead of words
        # many exampels in the datasets contain few words that losing one or more words can alter the emotions completely
        self.add_module("embed_dropout", nn.Dropout2d(embed_dropout_rate))
        self.add_module(
            "lstm_0",
            LSTMHardSigmoid(
                embedding_dim, hidden_size, batch_first=True, bidirectional=True
            ),
        )
        self.add_module(
            "lstm_1",
            LSTMHardSigmoid(
                hidden_size * 2, hidden_size, batch_first=True, bidirectional=True
            ),
        )
        self.add_module(
            "attention_layer",
            TorchmojiAttention(
                attention_size=attention_size, return_attention=return_attention
            ),
        )
        if not feature_output:
            self.add_module("final_dropout", nn.Dropout(final_dropout_rate))
            if output_logits:
                self.add_module(
                    "output_layer",
                    nn.Sequential(
                        nn.Linear(
                            attention_size, nb_classes if self.nb_classes > 2 else 1
                        )
                    ),
                )
            else:
                self.add_module(
                    "output_layer",
                    nn.Sequential(
                        nn.Linear(
                            attention_size, nb_classes if self.nb_classes > 2 else 1
                        ),
                        nn.Softmax() if self.nb_classes > 2 else nn.Sigmoid(),
                    ),
                )
        self.init_weights()
        # Put model in evaluation mode by default
        self.eval()

    def init_weights(self):
        """
        Here we reproduce Keras default initialization weights for consistency with Keras version
        """
        ih = (
            param.data for name, param in self.named_parameters() if "weight_ih" in name
        )
        hh = (
            param.data for name, param in self.named_parameters() if "weight_hh" in name
        )
        b = (param.data for name, param in self.named_parameters() if "bias" in name)
        nn.init.uniform(self.embed.weight.data, a=-0.5, b=0.5)
        for t in ih:
            nn.init.xavier_uniform(t)
        for t in hh:
            nn.init.orthogonal(t)
        for t in b:
            nn.init.constant(t, 0)
        if not self.feature_output:
            nn.init.xavier_uniform(self.output_layer[0].weight.data)

    def forward(self, input_seqs):
        """Forward pass.

        # Arguments:
            input_seqs: Can be one of Numpy array, Torch.LongTensor, Torch.Variable, Torch.PackedSequence.

        # Return:
            Same format as input format (except for PackedSequence returned as Variable).
        """
        # Check if we have Torch.LongTensor inputs or not Torch.Variable (assume Numpy array in this case), take note to return same format
        return_numpy = False
        return_tensor = False
        if isinstance(input_seqs, (torch.LongTensor, torch.cuda.LongTensor)):
            input_seqs = Variable(input_seqs)
            return_tensor = True
        elif not isinstance(input_seqs, Variable):
            input_seqs = Variable(torch.from_numpy(input_seqs.astype("int64")).long())
            return_numpy = True

        # If we don't have a packed inputs, let's pack it
        reorder_output = False
        if not isinstance(input_seqs, PackedSequence):
            ho = self.lstm_0.weight_hh_l0.data.new(
                2, input_seqs.size()[0], self.hidden_size
            ).zero_()
            co = self.lstm_0.weight_hh_l0.data.new(
                2, input_seqs.size()[0], self.hidden_size
            ).zero_()

            # Reorder batch by sequence length
            input_lengths = torch.LongTensor(
                [
                    torch.max(input_seqs[i, :].data.nonzero()) + 1
                    for i in range(input_seqs.size()[0])
                ]
            )
            input_lengths, perm_idx = input_lengths.sort(0, descending=True)
            input_seqs = input_seqs[perm_idx][:, : input_lengths.max()]

            # Pack sequence and work on data tensor to reduce embeddings/dropout computations
            packed_input = pack_padded_sequence(
                input_seqs,
                input_lengths.cpu().numpy(),
                batch_first=True,
                enforce_sorted=False,
            )
            reorder_output = True
        else:
            ho = self.lstm_0.weight_hh_l0.data.data.new(
                2, input_seqs.size()[0], self.hidden_size
            ).zero_()
            co = self.lstm_0.weight_hh_l0.data.data.new(
                2, input_seqs.size()[0], self.hidden_size
            ).zero_()
            input_lengths = input_seqs.batch_sizes
            packed_input = input_seqs

        hidden = (Variable(ho, requires_grad=False), Variable(co, requires_grad=False))

        # Embed with an activation function to bound the values of the embeddings
        x = self.embed(packed_input.data)
        x = nn.Tanh()(x)

        # pyTorch 2D dropout2d operate on axis 1 which is fine for us
        x = self.embed_dropout(x)

        # Update packed sequence data for RNN
        packed_input = PackedSequence(x, packed_input.batch_sizes)

        # skip-connection from embedding to output eases gradient-flow and allows access to lower-level features
        # ordering of the way the merge is done is important for consistency with the pretrained model
        lstm_0_output, _ = self.lstm_0(packed_input, hidden)
        lstm_1_output, _ = self.lstm_1(lstm_0_output, hidden)

        # Update packed sequence data for attention layer
        packed_input = PackedSequence(
            torch.cat(
                (lstm_1_output.data, lstm_0_output.data, packed_input.data), dim=1
            ),
            packed_input.batch_sizes,
        )

        input_seqs, _ = pad_packed_sequence(packed_input, batch_first=True)

        x, att_weights = self.attention_layer(input_seqs, input_lengths)

        # output class probabilities or penultimate feature vector
        if not self.feature_output:
            x = self.final_dropout(x)
            outputs = self.output_layer(x)
        else:
            outputs = x

        # Reorder output if needed
        if reorder_output:
            reorered = Variable(outputs.data.new(outputs.size()))
            reorered[perm_idx] = outputs
            outputs = reorered

        # Adapt return format if needed
        if return_tensor:
            outputs = outputs.data
        if return_numpy:
            outputs = outputs.data.numpy()

        if self.return_attention:
            return outputs, att_weights
        else:
            return outputs


def load_specific_weights(
    model, weight_path, exclude_names=[], extend_embedding=0, verbose=True
):
    """Loads model weights from the given file path, excluding any
        given layers.

    # Arguments:
        model: Model whose weights should be loaded.
        weight_path: Path to file containing model weights.
        exclude_names: List of layer names whose weights should not be loaded.
        extend_embedding: Number of new words being added to vocabulary.
        verbose: Verbosity flag.

    # Raises:
        ValueError if the file at weight_path does not exist.
    """
    if not exists(weight_path):
        raise ValueError(
            "ERROR (load_weights): The weights file at {} does "
            "not exist. Refer to the README for instructions.".format(weight_path)
        )

    if extend_embedding and "embed" in exclude_names:
        raise ValueError(
            "ERROR (load_weights): Cannot extend a vocabulary "
            "without loading the embedding weights."
        )

    # Copy only weights from the temporary model that are wanted
    # for the specific task (e.g. the Softmax is often ignored)
    weights = torch.load(weight_path)
    for key, weight in weights.items():
        if any(excluded in key for excluded in exclude_names):
            if verbose:
                print("Ignoring weights for {}".format(key))
            continue

        try:
            model_w = model.state_dict()[key]
        except KeyError:
            raise KeyError(
                "Weights had parameters {},".format(key)
                + " but could not find this parameters in model."
            )

        if verbose:
            print("Loading weights for {}".format(key))

        # extend embedding layer to allow new randomly initialized words
        # if requested. Otherwise, just load the weights for the layer.
        if "embed" in key and extend_embedding > 0:
            weight = torch.cat((weight, model_w[NB_TOKENS:, :]), dim=0)
            if verbose:
                print(
                    "Extended vocabulary for embedding layer "
                    + "from {} to {} tokens.".format(
                        NB_TOKENS, NB_TOKENS + extend_embedding
                    )
                )
        try:
            model_w.copy_(weight)
        except:
            print(
                "While copying the weigths named {}, whose dimensions in the model are"
                " {} and whose dimensions in the saved file are {}, ...".format(
                    key, model_w.size(), weight.size()
                )
            )
            raise


# torchmoji/finetuning.py

""" Finetuning functions for doing transfer learning to new datasets.
"""

try:
    unicode
    IS_PYTHON2 = True
except NameError:
    unicode = str
    IS_PYTHON2 = False


def load_benchmark(path, vocab, extend_with=0):
    """Loads the given benchmark dataset.

        Tokenizes the texts using the provided vocabulary, extending it with
        words from the training dataset if extend_with > 0. Splits them into
        three lists: training, validation and testing (in that order).

        Also calculates the maximum length of the texts and the
        suggested batch_size.

    # Arguments:
        path: Path to the dataset to be loaded.
        vocab: Vocabulary to be used for tokenizing texts.
        extend_with: If > 0, the vocabulary will be extended with up to
            extend_with tokens from the training set before tokenizing.

    # Returns:
        A dictionary with the following fields:
            texts: List of three lists, containing tokenized inputs for
                training, validation and testing (in that order).
            labels: List of three lists, containing labels for training,
                validation and testing (in that order).
            added: Number of tokens added to the vocabulary.
            batch_size: Batch size.
            maxlen: Maximum length of an input.
    """
    # Pre-processing dataset
    with open(path, "rb") as dataset:
        if IS_PYTHON2:
            data = pickle.load(dataset)
        else:
            data = pickle.load(dataset, fix_imports=True)

    # Decode data
    try:
        texts = [unicode(x) for x in data["texts"]]
    except UnicodeDecodeError:
        texts = [x.decode("utf-8") for x in data["texts"]]

    # Extract labels
    labels = [x["label"] for x in data["info"]]

    batch_size, maxlen = calculate_batchsize_maxlen(texts)

    st = SentenceTokenizer(vocab, maxlen)

    # Split up dataset. Extend the existing vocabulary with up to extend_with
    # tokens from the training dataset.
    texts, labels, added = st.split_train_val_test(
        texts,
        labels,
        [data["train_ind"], data["val_ind"], data["test_ind"]],
        extend_with=extend_with,
    )
    return {
        "texts": texts,
        "labels": labels,
        "added": added,
        "batch_size": batch_size,
        "maxlen": maxlen,
    }


def calculate_batchsize_maxlen(texts):
    """Calculates the maximum length in the provided texts and a suitable
        batch size. Rounds up maxlen to the nearest multiple of ten.

    # Arguments:
        texts: List of inputs.

    # Returns:
        Batch size,
        max length
    """

    def roundup(x):
        return int(math.ceil(x / 10.0)) * 10

    # Calculate max length of sequences considered
    # Adjust batch_size accordingly to prevent GPU overflow
    lengths = [len(tokenize(t)) for t in texts]
    maxlen = roundup(np.percentile(lengths, 80.0))
    batch_size = 250 if maxlen <= 100 else 50
    return batch_size, maxlen


def freeze_layers(model, unfrozen_types=[], unfrozen_keyword=None):
    """Freezes all layers in the given model, except for ones that are
        explicitly specified to not be frozen.

    # Arguments:
        model: Model whose layers should be modified.
        unfrozen_types: List of layer types which shouldn't be frozen.
        unfrozen_keyword: Name keywords of layers that shouldn't be frozen.

    # Returns:
        Model with the selected layers frozen.
    """
    # Get trainable modules
    trainable_modules = [
        (n, m)
        for n, m in model.named_children()
        if len([id(p) for p in m.parameters()]) != 0
    ]
    for name, module in trainable_modules:
        trainable = any(typ in str(module) for typ in unfrozen_types) or (
            unfrozen_keyword is not None and unfrozen_keyword.lower() in name.lower()
        )
        change_trainable(module, trainable, verbose=False)
    return model


def change_trainable(module, trainable, verbose=False):
    """Helper method that freezes or unfreezes a given layer.

    # Arguments:
        module: Module to be modified.
        trainable: Whether the layer should be frozen or unfrozen.
        verbose: Verbosity flag.
    """

    if verbose:
        print("Changing MODULE", module, "to trainable =", trainable)
    for name, param in module.named_parameters():
        if verbose:
            print("Setting weight", name, "to trainable =", trainable)
        param.requires_grad = trainable

    if verbose:
        action = "Unfroze" if trainable else "Froze"
        if verbose:
            print("{} {}".format(action, module))


def find_f1_threshold(model, val_gen, test_gen, average="binary"):
    """Choose a threshold for F1 based on the validation dataset
        (see https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4442797/
        for details on why to find another threshold than simply 0.5)

    # Arguments:
        model: pyTorch model
        val_gen: Validation set dataloader.
        test_gen: Testing set dataloader.

    # Returns:
        F1 score for the given data and
        the corresponding F1 threshold
    """
    thresholds = np.arange(0.01, 0.5, step=0.01)
    f1_scores = []

    model.eval()
    val_out = [(y, model(X)) for X, y in val_gen]
    y_val, y_pred_val = (list(t) for t in zip(*val_out))

    test_out = [(y, model(X)) for X, y in test_gen]
    y_test, y_pred_test = (list(t) for t in zip(*val_out))

    for t in thresholds:
        y_pred_val_ind = y_pred_val > t
        f1_val = f1_score(y_val, y_pred_val_ind, average=average)
        f1_scores.append(f1_val)

    best_t = thresholds[np.argmax(f1_scores)]
    y_pred_ind = y_pred_test > best_t
    f1_test = f1_score(y_test, y_pred_ind, average=average)
    return f1_test, best_t


def finetune(
    model,
    texts,
    labels,
    nb_classes,
    batch_size,
    method,
    metric="acc",
    epoch_size=5000,
    nb_epochs=1000,
    embed_l2=1e-6,
    verbose=1,
    weights_dir="./weights",
):
    """Compiles and finetunes the given pytorch model.

    # Arguments:
        model: Model to be finetuned
        texts: List of three lists, containing tokenized inputs for training,
            validation and testing (in that order).
        labels: List of three lists, containing labels for training,
            validation and testing (in that order).
        nb_classes: Number of classes in the dataset.
        batch_size: Batch size.
        method: Finetuning method to be used. For available methods, see
            FINETUNING_METHODS in global_variables.py.
        metric: Evaluation metric to be used. For available metrics, see
            FINETUNING_METRICS in global_variables.py.
        epoch_size: Number of samples in an epoch.
        nb_epochs: Number of epochs. Doesn't matter much as early stopping is used.
        embed_l2: L2 regularization for the embedding layer.
        verbose: Verbosity flag.

    # Returns:
        Model after finetuning,
        score after finetuning using the provided metric.
    """

    if method not in FINETUNING_METHODS:
        raise ValueError(
            "ERROR (finetune): Invalid method parameter. "
            "Available options: {}".format(FINETUNING_METHODS)
        )
    if metric not in FINETUNING_METRICS:
        raise ValueError(
            "ERROR (finetune): Invalid metric parameter. "
            "Available options: {}".format(FINETUNING_METRICS)
        )

    train_gen = get_data_loader(
        texts[0],
        labels[0],
        batch_size,
        extended_batch_sampler=True,
        epoch_size=epoch_size,
    )
    val_gen = get_data_loader(
        texts[1], labels[1], batch_size, extended_batch_sampler=False
    )
    test_gen = get_data_loader(
        texts[2], labels[2], batch_size, extended_batch_sampler=False
    )

    checkpoint_path = "{}/torchmoji-checkpoint-{}.bin".format(
        weights_dir, str(uuid.uuid4())
    )

    if method in ["last", "new"]:
        lr = 0.001
    elif method in ["full", "chain-thaw"]:
        lr = 0.0001

    loss_op = nn.BCEWithLogitsLoss() if nb_classes <= 2 else nn.CrossEntropyLoss()

    # Freeze layers if using last
    if method == "last":
        model = freeze_layers(model, unfrozen_keyword="output_layer")

    # Define optimizer, for chain-thaw we define it later (after freezing)
    if method == "last":
        adam = optim.Adam((p for p in model.parameters() if p.requires_grad), lr=lr)
    elif method in ["full", "new"]:
        # Add L2 regulation on embeddings only
        embed_params_id = [id(p) for p in model.embed.parameters()]
        output_layer_params_id = [id(p) for p in model.output_layer.parameters()]
        base_params = [
            p
            for p in model.parameters()
            if id(p) not in embed_params_id
            and id(p) not in output_layer_params_id
            and p.requires_grad
        ]
        embed_params = [
            p
            for p in model.parameters()
            if id(p) in embed_params_id and p.requires_grad
        ]
        output_layer_params = [
            p
            for p in model.parameters()
            if id(p) in output_layer_params_id and p.requires_grad
        ]
        adam = optim.Adam(
            [
                {"params": base_params},
                {"params": embed_params, "weight_decay": embed_l2},
                {"params": output_layer_params, "lr": 0.001},
            ],
            lr=lr,
        )

    # Training
    if verbose:
        print("Method:  {}".format(method))
        print("Metric:  {}".format(metric))
        print("Classes: {}".format(nb_classes))

    if method == "chain-thaw":
        result = chain_thaw(
            model,
            train_gen,
            val_gen,
            test_gen,
            nb_epochs,
            checkpoint_path,
            loss_op,
            embed_l2=embed_l2,
            evaluate=metric,
            verbose=verbose,
        )
    else:
        result = tune_trainable(
            model,
            loss_op,
            adam,
            train_gen,
            val_gen,
            test_gen,
            nb_epochs,
            checkpoint_path,
            evaluate=metric,
            verbose=verbose,
        )
    return model, result


def tune_trainable(
    model,
    loss_op,
    optim_op,
    train_gen,
    val_gen,
    test_gen,
    nb_epochs,
    checkpoint_path,
    patience=5,
    evaluate="acc",
    verbose=2,
):
    """Finetunes the given model using the accuracy measure.

    # Arguments:
        model: Model to be finetuned.
        nb_classes: Number of classes in the given dataset.
        train: Training data, given as a tuple of (inputs, outputs)
        val: Validation data, given as a tuple of (inputs, outputs)
        test: Testing data, given as a tuple of (inputs, outputs)
        epoch_size: Number of samples in an epoch.
        nb_epochs: Number of epochs.
        batch_size: Batch size.
        checkpoint_weight_path: Filepath where weights will be checkpointed to
            during training. This file will be rewritten by the function.
        patience: Patience for callback methods.
        evaluate: Evaluation method to use. Can be 'acc' or 'weighted_f1'.
        verbose: Verbosity flag.

    # Returns:
        Accuracy of the trained model, ONLY if 'evaluate' is set.
    """
    if verbose:
        print(
            "Trainable weights: {}".format(
                [n for n, p in model.named_parameters() if p.requires_grad]
            )
        )
        print("Training...")
        if evaluate == "acc":
            print(
                "Evaluation on test set prior training:",
                evaluate_using_acc(model, test_gen),
            )
        elif evaluate == "weighted_f1":
            print(
                "Evaluation on test set prior training:",
                evaluate_using_weighted_f1(model, test_gen, val_gen),
            )

    fit_model(
        model,
        loss_op,
        optim_op,
        train_gen,
        val_gen,
        nb_epochs,
        checkpoint_path,
        patience,
    )

    # Reload the best weights found to avoid overfitting
    # Wait a bit to allow proper closing of weights file
    sleep(1)
    model.load_state_dict(torch.load(checkpoint_path))
    if verbose >= 2:
        print("Loaded weights from {}".format(checkpoint_path))

    if evaluate == "acc":
        return evaluate_using_acc(model, test_gen)
    elif evaluate == "weighted_f1":
        return evaluate_using_weighted_f1(model, test_gen, val_gen)


def evaluate_using_weighted_f1(model, test_gen, val_gen):
    """Evaluation function using macro weighted F1 score.

    # Arguments:
        model: Model to be evaluated.
        X_test: Inputs of the testing set.
        y_test: Outputs of the testing set.
        X_val: Inputs of the validation set.
        y_val: Outputs of the validation set.
        batch_size: Batch size.

    # Returns:
        Weighted F1 score of the given model.
    """
    # Evaluate on test and val data
    f1_test, _ = find_f1_threshold(model, test_gen, val_gen, average="weighted_f1")
    return f1_test


def evaluate_using_acc(model, test_gen):
    """Evaluation function using accuracy.

    # Arguments:
        model: Model to be evaluated.
        test_gen: Testing data iterator (DataLoader)

    # Returns:
        Accuracy of the given model.
    """

    # Validate on test_data
    model.eval()
    accs = []
    for i, data in enumerate(test_gen):
        x, y = data
        outs = model(x)
        if model.nb_classes > 2:
            pred = torch.max(outs, 1)[1]
            acc = accuracy_score(y.squeeze().numpy(), pred.squeeze().numpy())
        else:
            pred = (outs >= 0).long()
            acc = (pred == y).double().sum() / len(pred)
        accs.append(acc)
    return np.mean(accs)


def chain_thaw(
    model,
    train_gen,
    val_gen,
    test_gen,
    nb_epochs,
    checkpoint_path,
    loss_op,
    patience=5,
    initial_lr=0.001,
    next_lr=0.0001,
    embed_l2=1e-6,
    evaluate="acc",
    verbose=1,
):
    """Finetunes given model using chain-thaw and evaluates using accuracy.

    # Arguments:
        model: Model to be finetuned.
        train: Training data, given as a tuple of (inputs, outputs)
        val: Validation data, given as a tuple of (inputs, outputs)
        test: Testing data, given as a tuple of (inputs, outputs)
        batch_size: Batch size.
        loss: Loss function to be used during training.
        epoch_size: Number of samples in an epoch.
        nb_epochs: Number of epochs.
        checkpoint_weight_path: Filepath where weights will be checkpointed to
            during training. This file will be rewritten by the function.
        initial_lr: Initial learning rate. Will only be used for the first
            training step (i.e. the output_layer layer)
        next_lr: Learning rate for every subsequent step.
        seed: Random number generator seed.
        verbose: Verbosity flag.
        evaluate: Evaluation method to use. Can be 'acc' or 'weighted_f1'.

    # Returns:
        Accuracy of the finetuned model.
    """
    if verbose:
        print("Training..")

    # Train using chain-thaw
    train_by_chain_thaw(
        model,
        train_gen,
        val_gen,
        loss_op,
        patience,
        nb_epochs,
        checkpoint_path,
        initial_lr,
        next_lr,
        embed_l2,
        verbose,
    )

    if evaluate == "acc":
        return evaluate_using_acc(model, test_gen)
    elif evaluate == "weighted_f1":
        return evaluate_using_weighted_f1(model, test_gen, val_gen)


def train_by_chain_thaw(
    model,
    train_gen,
    val_gen,
    loss_op,
    patience,
    nb_epochs,
    checkpoint_path,
    initial_lr=0.001,
    next_lr=0.0001,
    embed_l2=1e-6,
    verbose=1,
):
    """Finetunes model using the chain-thaw method.

    This is done as follows:
    1) Freeze every layer except the last (output_layer) layer and train it.
    2) Freeze every layer except the first layer and train it.
    3) Freeze every layer except the second etc., until the second last layer.
    4) Unfreeze all layers and train entire model.

    # Arguments:
        model: Model to be trained.
        train_gen: Training sample generator.
        val_data: Validation data.
        loss: Loss function to be used.
        finetuning_args: Training early stopping and checkpoint saving parameters
        epoch_size: Number of samples in an epoch.
        nb_epochs: Number of epochs.
        checkpoint_weight_path: Where weight checkpoints should be saved.
        batch_size: Batch size.
        initial_lr: Initial learning rate. Will only be used for the first
            training step (i.e. the output_layer layer)
        next_lr: Learning rate for every subsequent step.
        verbose: Verbosity flag.
    """
    # Get trainable layers
    layers = [m for m in model.children() if len([id(p) for p in m.parameters()]) != 0]

    # Bring last layer to front
    layers.insert(0, layers.pop(len(layers) - 1))

    # Add None to the end to signify finetuning all layers
    layers.append(None)

    lr = None
    # Finetune each layer one by one and finetune all of them at once
    # at the end
    for layer in layers:
        if lr is None:
            lr = initial_lr
        elif lr == initial_lr:
            lr = next_lr

        # Freeze all except current layer
        for _layer in layers:
            if _layer is not None:
                trainable = _layer == layer or layer is None
                change_trainable(_layer, trainable=trainable, verbose=False)

        # Verify we froze the right layers
        for _layer in model.children():
            assert (
                all(p.requires_grad == (_layer == layer) for p in _layer.parameters())
                or layer is None
            )

        if verbose:
            if layer is None:
                print("Finetuning all layers")
            else:
                print("Finetuning {}".format(layer))

        special_params = [id(p) for p in model.embed.parameters()]
        base_params = [
            p
            for p in model.parameters()
            if id(p) not in special_params and p.requires_grad
        ]
        embed_parameters = [
            p for p in model.parameters() if id(p) in special_params and p.requires_grad
        ]
        adam = optim.Adam(
            [
                {"params": base_params},
                {"params": embed_parameters, "weight_decay": embed_l2},
            ],
            lr=lr,
        )

        fit_model(
            model,
            loss_op,
            adam,
            train_gen,
            val_gen,
            nb_epochs,
            checkpoint_path,
            patience,
        )

        # Reload the best weights found to avoid overfitting
        # Wait a bit to allow proper closing of weights file
        sleep(1)
        model.load_state_dict(torch.load(checkpoint_path))
        if verbose >= 2:
            print("Loaded weights from {}".format(checkpoint_path))


def calc_loss(loss_op, pred, yv):
    if type(loss_op) is nn.CrossEntropyLoss:
        return loss_op(pred.squeeze(), yv.squeeze())
    else:
        return loss_op(pred.squeeze(), yv.squeeze().float())


def fit_model(
    model, loss_op, optim_op, train_gen, val_gen, epochs, checkpoint_path, patience
):
    """Analog to Keras fit_generator function.

    # Arguments:
        model: Model to be finetuned.
        loss_op: loss operation (BCEWithLogitsLoss or CrossEntropy for e.g.)
        optim_op: optimization operation (Adam e.g.)
        train_gen: Training data iterator (DataLoader)
        val_gen: Validation data iterator (DataLoader)
        epochs: Number of epochs.
        checkpoint_path: Filepath where weights will be checkpointed to
            during training. This file will be rewritten by the function.
        patience: Patience for callback methods.
        verbose: Verbosity flag.

    # Returns:
        Accuracy of the trained model, ONLY if 'evaluate' is set.
    """
    # Save original checkpoint
    torch.save(model.state_dict(), checkpoint_path)

    model.eval()
    best_loss = np.mean(
        [
            calc_loss(loss_op, model(Variable(xv)), Variable(yv)).data.cpu().numpy()[0]
            for xv, yv in val_gen
        ]
    )
    print("original val loss", best_loss)

    epoch_without_impr = 0
    for epoch in range(epochs):
        for i, data in enumerate(train_gen):
            X_train, y_train = data
            X_train = Variable(X_train, requires_grad=False)
            y_train = Variable(y_train, requires_grad=False)
            model.train()
            optim_op.zero_grad()
            output = model(X_train)
            loss = calc_loss(loss_op, output, y_train)
            loss.backward()
            clip_grad_norm(model.parameters(), 1)
            optim_op.step()

            acc = evaluate_using_acc(model, [(X_train.data, y_train.data)])
            print(
                "== Epoch",
                epoch,
                "step",
                i,
                "train loss",
                loss.data.cpu().numpy()[0],
                "train acc",
                acc,
            )

        model.eval()
        acc = evaluate_using_acc(model, val_gen)
        print("val acc", acc)

        val_loss = np.mean(
            [
                calc_loss(loss_op, model(Variable(xv)), Variable(yv))
                .data.cpu()
                .numpy()[0]
                for xv, yv in val_gen
            ]
        )
        print("val loss", val_loss)
        if best_loss is not None and val_loss >= best_loss:
            epoch_without_impr += 1
            print("No improvement over previous best loss: ", best_loss)

        # Save checkpoint
        if best_loss is None or val_loss < best_loss:
            best_loss = val_loss
            torch.save(model.state_dict(), checkpoint_path)
            print("Saving model at", checkpoint_path)

        # Early stopping
        if epoch_without_impr >= patience:
            break


def get_data_loader(
    X_in,
    y_in,
    batch_size,
    extended_batch_sampler=True,
    epoch_size=25000,
    upsample=False,
    seed=42,
):
    """Returns a dataloader that enables larger epochs on small datasets and
        has upsampling functionality.

    # Arguments:
        X_in: Inputs of the given dataset.
        y_in: Outputs of the given dataset.
        batch_size: Batch size.
        epoch_size: Number of samples in an epoch.
        upsample: Whether upsampling should be done. This flag should only be
            set on binary class problems.

    # Returns:
        DataLoader.
    """
    dataset = DeepMojiDataset(X_in, y_in)

    if extended_batch_sampler:
        batch_sampler = DeepMojiBatchSampler(
            y_in, batch_size, epoch_size=epoch_size, upsample=upsample, seed=seed
        )
    else:
        batch_sampler = BatchSampler(
            SequentialSampler(y_in), batch_size, drop_last=False
        )

    return DataLoader(dataset, batch_sampler=batch_sampler, num_workers=0)


class DeepMojiDataset(Dataset):
    """A simple Dataset class.

    # Arguments:
        X_in: Inputs of the given dataset.
        y_in: Outputs of the given dataset.

    # __getitem__ output:
        (torch.LongTensor, torch.LongTensor)
    """

    def __init__(self, X_in, y_in):
        # Check if we have Torch.LongTensor inputs (assume Numpy array otherwise)
        if not isinstance(X_in, torch.LongTensor):
            X_in = torch.from_numpy(X_in.astype("int64")).long()
        if not isinstance(y_in, torch.LongTensor):
            y_in = torch.from_numpy(y_in.astype("int64")).long()

        self.X_in = torch.split(X_in, 1, dim=0)
        self.y_in = torch.split(y_in, 1, dim=0)

    def __len__(self):
        return len(self.X_in)

    def __getitem__(self, idx):
        return self.X_in[idx].squeeze(), self.y_in[idx].squeeze()


class DeepMojiBatchSampler(object):
    """A Batch sampler that enables larger epochs on small datasets and
        has upsampling functionality.

    # Arguments:
        y_in: Labels of the dataset.
        batch_size: Batch size.
        epoch_size: Number of samples in an epoch.
        upsample: Whether upsampling should be done. This flag should only be
            set on binary class problems.
        seed: Random number generator seed.

    # __iter__ output:
        iterator of lists (batches) of indices in the dataset
    """

    def __init__(self, y_in, batch_size, epoch_size, upsample, seed):
        self.batch_size = batch_size
        self.epoch_size = epoch_size
        self.upsample = upsample

        np.random.seed(seed)

        if upsample:
            # Should only be used on binary class problems
            assert len(y_in.shape) == 1
            neg = np.where(y_in.numpy() == 0)[0]
            pos = np.where(y_in.numpy() == 1)[0]
            assert epoch_size % 2 == 0
            samples_pr_class = int(epoch_size / 2)
        else:
            ind = range(len(y_in))

        if not upsample:
            # Randomly sample observations in a balanced way
            self.sample_ind = np.random.choice(ind, epoch_size, replace=True)
        else:
            # Randomly sample observations in a balanced way
            sample_neg = np.random.choice(neg, samples_pr_class, replace=True)
            sample_pos = np.random.choice(pos, samples_pr_class, replace=True)
            concat_ind = np.concatenate((sample_neg, sample_pos), axis=0)

            # Shuffle to avoid labels being in specific order
            # (all negative then positive)
            p = np.random.permutation(len(concat_ind))
            self.sample_ind = concat_ind[p]

            label_dist = np.mean(y_in.numpy()[self.sample_ind])
            assert label_dist > 0.45
            assert label_dist < 0.55

    def __iter__(self):
        # Hand-off data using batch_size
        for i in range(int(self.epoch_size / self.batch_size)):
            start = i * self.batch_size
            end = min(start + self.batch_size, self.epoch_size)
            yield self.sample_ind[start:end]

    def __len__(self):
        # Take care of the last (maybe incomplete) batch
        return (self.epoch_size + self.batch_size - 1) // self.batch_size


# torchmoji/class_avg_finetuning.py
""" Class average finetuning functions. Before using any of these finetuning
    functions, ensure that the model is set up with nb_classes=2.
"""


def relabel(y, current_label_nr, nb_classes):
    """Makes a binary classification for a specific class in a
        multi-class dataset.

    # Arguments:
        y: Outputs to be relabelled.
        current_label_nr: Current label number.
        nb_classes: Total number of classes.

    # Returns:
        Relabelled outputs of a given multi-class dataset into a binary
        classification dataset.
    """

    # Handling binary classification
    if nb_classes == 2 and len(y.shape) == 1:
        return y

    y_new = np.zeros(len(y))
    y_cut = y[:, current_label_nr]
    label_pos = np.where(y_cut == 1)[0]
    y_new[label_pos] = 1
    return y_new


def class_avg_finetune(
    model,
    texts,
    labels,
    nb_classes,
    batch_size,
    method,
    epoch_size=5000,
    nb_epochs=1000,
    embed_l2=1e-6,
    verbose=True,
    weights_dir="./weights",
):
    """Compiles and finetunes the given model.

    # Arguments:
        model: Model to be finetuned
        texts: List of three lists, containing tokenized inputs for training,
            validation and testing (in that order).
        labels: List of three lists, containing labels for training,
            validation and testing (in that order).
        nb_classes: Number of classes in the dataset.
        batch_size: Batch size.
        method: Finetuning method to be used. For available methods, see
            FINETUNING_METHODS in global_variables.py. Note that the model
            should be defined accordingly (see docstring for torchmoji_transfer())
        epoch_size: Number of samples in an epoch.
        nb_epochs: Number of epochs. Doesn't matter much as early stopping is used.
        embed_l2: L2 regularization for the embedding layer.
        verbose: Verbosity flag.

    # Returns:
        Model after finetuning,
        score after finetuning using the class average F1 metric.
    """

    if method not in FINETUNING_METHODS:
        raise ValueError(
            "ERROR (class_avg_tune_trainable): "
            "Invalid method parameter. "
            "Available options: {}".format(FINETUNING_METHODS)
        )

    (X_train, y_train) = (texts[0], labels[0])
    (X_val, y_val) = (texts[1], labels[1])
    (X_test, y_test) = (texts[2], labels[2])

    checkpoint_path = "{}/torchmoji-checkpoint-{}.bin".format(
        weights_dir, str(uuid.uuid4())
    )

    f1_init_path = "{}/torchmoji-f1-init-{}.bin".format(weights_dir, str(uuid.uuid4()))

    if method in ["last", "new"]:
        lr = 0.001
    elif method in ["full", "chain-thaw"]:
        lr = 0.0001

    loss_op = nn.BCEWithLogitsLoss()

    # Freeze layers if using last
    if method == "last":
        model = freeze_layers(model, unfrozen_keyword="output_layer")

    # Define optimizer, for chain-thaw we define it later (after freezing)
    if method == "last":
        adam = optim.Adam((p for p in model.parameters() if p.requires_grad), lr=lr)
    elif method in ["full", "new"]:
        # Add L2 regulation on embeddings only
        special_params = [id(p) for p in model.embed.parameters()]
        base_params = [
            p
            for p in model.parameters()
            if id(p) not in special_params and p.requires_grad
        ]
        embed_parameters = [
            p for p in model.parameters() if id(p) in special_params and p.requires_grad
        ]
        adam = optim.Adam(
            [
                {"params": base_params},
                {"params": embed_parameters, "weight_decay": embed_l2},
            ],
            lr=lr,
        )

    # Training
    if verbose:
        print("Method:  {}".format(method))
        print("Classes: {}".format(nb_classes))

    if method == "chain-thaw":
        result = class_avg_chainthaw(
            model,
            nb_classes=nb_classes,
            loss_op=loss_op,
            train=(X_train, y_train),
            val=(X_val, y_val),
            test=(X_test, y_test),
            batch_size=batch_size,
            epoch_size=epoch_size,
            nb_epochs=nb_epochs,
            checkpoint_weight_path=checkpoint_path,
            f1_init_weight_path=f1_init_path,
            verbose=verbose,
        )
    else:
        result = class_avg_tune_trainable(
            model,
            nb_classes=nb_classes,
            loss_op=loss_op,
            optim_op=adam,
            train=(X_train, y_train),
            val=(X_val, y_val),
            test=(X_test, y_test),
            epoch_size=epoch_size,
            nb_epochs=nb_epochs,
            batch_size=batch_size,
            init_weight_path=f1_init_path,
            checkpoint_weight_path=checkpoint_path,
            verbose=verbose,
        )
    return model, result


def prepare_labels(y_train, y_val, y_test, iter_i, nb_classes):
    # Relabel into binary classification
    y_train_new = relabel(y_train, iter_i, nb_classes)
    y_val_new = relabel(y_val, iter_i, nb_classes)
    y_test_new = relabel(y_test, iter_i, nb_classes)
    return y_train_new, y_val_new, y_test_new


def prepare_generators(X_train, y_train_new, X_val, y_val_new, batch_size, epoch_size):
    # Create sample generators
    # Make a fixed validation set to avoid fluctuations in validation
    train_gen = get_data_loader(
        X_train, y_train_new, batch_size, extended_batch_sampler=True
    )
    val_gen = get_data_loader(X_val, y_val_new, epoch_size, extended_batch_sampler=True)
    X_val_resamp, y_val_resamp = next(iter(val_gen))
    return train_gen, X_val_resamp, y_val_resamp


def class_avg_tune_trainable(
    model,
    nb_classes,
    loss_op,
    optim_op,
    train,
    val,
    test,
    epoch_size,
    nb_epochs,
    batch_size,
    init_weight_path,
    checkpoint_weight_path,
    patience=5,
    verbose=True,
):
    """Finetunes the given model using the F1 measure.

    # Arguments:
        model: Model to be finetuned.
        nb_classes: Number of classes in the given dataset.
        train: Training data, given as a tuple of (inputs, outputs)
        val: Validation data, given as a tuple of (inputs, outputs)
        test: Testing data, given as a tuple of (inputs, outputs)
        epoch_size: Number of samples in an epoch.
        nb_epochs: Number of epochs.
        batch_size: Batch size.
        init_weight_path: Filepath where weights will be initially saved before
            training each class. This file will be rewritten by the function.
        checkpoint_weight_path: Filepath where weights will be checkpointed to
            during training. This file will be rewritten by the function.
        verbose: Verbosity flag.

    # Returns:
        F1 score of the trained model
    """
    total_f1 = 0
    nb_iter = nb_classes if nb_classes > 2 else 1

    # Unpack args
    X_train, y_train = train
    X_val, y_val = val
    X_test, y_test = test

    # Save and reload initial weights after running for
    # each class to avoid learning across classes
    torch.save(model.state_dict(), init_weight_path)
    for i in range(nb_iter):
        if verbose:
            print("Iteration number {}/{}".format(i + 1, nb_iter))

        model.load_state_dict(torch.load(init_weight_path))
        y_train_new, y_val_new, y_test_new = prepare_labels(
            y_train, y_val, y_test, i, nb_classes
        )
        train_gen, X_val_resamp, y_val_resamp = prepare_generators(
            X_train, y_train_new, X_val, y_val_new, batch_size, epoch_size
        )

        if verbose:
            print("Training..")
        fit_model(
            model,
            loss_op,
            optim_op,
            train_gen,
            [(X_val_resamp, y_val_resamp)],
            nb_epochs,
            checkpoint_weight_path,
            patience,
            verbose=0,
        )

        # Reload the best weights found to avoid overfitting
        # Wait a bit to allow proper closing of weights file
        sleep(1)
        model.load_state_dict(torch.load(checkpoint_weight_path))

        # Evaluate
        y_pred_val = model(X_val).cpu().numpy()
        y_pred_test = model(X_test).cpu().numpy()

        f1_test, best_t = find_f1_threshold(
            y_val_new, y_pred_val, y_test_new, y_pred_test
        )
        if verbose:
            print("f1_test: {}".format(f1_test))
            print("best_t:  {}".format(best_t))
        total_f1 += f1_test

    return total_f1 / nb_iter


def class_avg_chainthaw(
    model,
    nb_classes,
    loss_op,
    train,
    val,
    test,
    batch_size,
    epoch_size,
    nb_epochs,
    checkpoint_weight_path,
    f1_init_weight_path,
    patience=5,
    initial_lr=0.001,
    next_lr=0.0001,
    verbose=True,
):
    """Finetunes given model using chain-thaw and evaluates using F1.
        For a dataset with multiple classes, the model is trained once for
        each class, relabeling those classes into a binary classification task.
        The result is an average of all F1 scores for each class.

    # Arguments:
        model: Model to be finetuned.
        nb_classes: Number of classes in the given dataset.
        train: Training data, given as a tuple of (inputs, outputs)
        val: Validation data, given as a tuple of (inputs, outputs)
        test: Testing data, given as a tuple of (inputs, outputs)
        batch_size: Batch size.
        loss: Loss function to be used during training.
        epoch_size: Number of samples in an epoch.
        nb_epochs: Number of epochs.
        checkpoint_weight_path: Filepath where weights will be checkpointed to
            during training. This file will be rewritten by the function.
        f1_init_weight_path: Filepath where weights will be saved to and
            reloaded from before training each class. This ensures that
            each class is trained independently. This file will be rewritten.
        initial_lr: Initial learning rate. Will only be used for the first
            training step (i.e. the softmax layer)
        next_lr: Learning rate for every subsequent step.
        seed: Random number generator seed.
        verbose: Verbosity flag.

    # Returns:
        Averaged F1 score.
    """

    # Unpack args
    X_train, y_train = train
    X_val, y_val = val
    X_test, y_test = test

    total_f1 = 0
    nb_iter = nb_classes if nb_classes > 2 else 1

    torch.save(model.state_dict(), f1_init_weight_path)

    for i in range(nb_iter):
        if verbose:
            print("Iteration number {}/{}".format(i + 1, nb_iter))

        model.load_state_dict(torch.load(f1_init_weight_path))
        y_train_new, y_val_new, y_test_new = prepare_labels(
            y_train, y_val, y_test, i, nb_classes
        )
        train_gen, X_val_resamp, y_val_resamp = prepare_generators(
            X_train, y_train_new, X_val, y_val_new, batch_size, epoch_size
        )

        if verbose:
            print("Training..")

        # Train using chain-thaw
        train_by_chain_thaw(
            model=model,
            train_gen=train_gen,
            val_gen=[(X_val_resamp, y_val_resamp)],
            loss_op=loss_op,
            patience=patience,
            nb_epochs=nb_epochs,
            checkpoint_path=checkpoint_weight_path,
            initial_lr=initial_lr,
            next_lr=next_lr,
            verbose=verbose,
        )

        # Evaluate
        y_pred_val = model(X_val).cpu().numpy()
        y_pred_test = model(X_test).cpu().numpy()

        f1_test, best_t = find_f1_threshold(
            y_val_new, y_pred_val, y_test_new, y_pred_test
        )

        if verbose:
            print("f1_test: {}".format(f1_test))
            print("best_t:  {}".format(best_t))
        total_f1 += f1_test

    return total_f1 / nb_iter


# torchmoji/filter_input.py


def read_english(path="english_words.txt", add_emojis=True):
    # read english words for filtering (includes emojis as part of set)
    english = set()
    with codecs.open(path, "r", "utf-8") as f:
        for line in f:
            line = line.strip().lower().replace("\n", "")
            if len(line):
                english.add(line)
    if add_emojis:
        for e in ALLOWED_EMOJIS:
            english.add(e)
    return english


def read_wanted_emojis(path="wanted_emojis.csv"):
    emojis = []
    with open(path, "rb") as f:
        reader = csv.reader(f)
        for line in reader:
            line = line[0].strip().replace("\n", "")
            line = line.decode("unicode-escape")
            emojis.append(line)
    return emojis


def read_non_english_users(path="unwanted_users.npz"):
    try:
        neu_set = set(np.load(path)["userids"])
    except IOError:
        neu_set = set()
    return neu_set


# torchmoji/filter_utils.py

try:
    unichr  # Python 2
except NameError:
    unichr = chr  # Python 3


AtMentionRegex = re.compile(RE_MENTION)
urlRegex = re.compile(RE_URL)

# from http://bit.ly/2rdjgjE (UTF-8 encodings and Unicode chars)
VARIATION_SELECTORS = [
    "\ufe00",
    "\ufe01",
    "\ufe02",
    "\ufe03",
    "\ufe04",
    "\ufe05",
    "\ufe06",
    "\ufe07",
    "\ufe08",
    "\ufe09",
    "\ufe0a",
    "\ufe0b",
    "\ufe0c",
    "\ufe0d",
    "\ufe0e",
    "\ufe0f",
]

# from https://stackoverflow.com/questions/92438/stripping-non-printable-characters-from-a-string-in-python
ALL_CHARS = (unichr(i) for i in range(sys.maxunicode))
CONTROL_CHARS = "".join(map(unichr, list(range(0, 32)) + list(range(127, 160))))
CONTROL_CHAR_REGEX = re.compile("[%s]" % re.escape(CONTROL_CHARS))


def is_special_token(word):
    equal = False
    for spec in SPECIAL_TOKENS:
        if word == spec:
            equal = True
            break
    return equal


def mostly_english(
    words,
    english,
    pct_eng_short=0.5,
    pct_eng_long=0.6,
    ignore_special_tokens=True,
    min_length=2,
):
    """Ensure text meets threshold for containing English words"""

    n_words = 0
    n_english = 0

    if english is None:
        return True, 0, 0

    for w in words:
        if len(w) < min_length:
            continue
        if punct_word(w):
            continue
        if ignore_special_tokens and is_special_token(w):
            continue
        n_words += 1
        if w in english:
            n_english += 1

    if n_words < 2:
        return True, n_words, n_english
    if n_words < 5:
        valid_english = n_english >= n_words * pct_eng_short
    else:
        valid_english = n_english >= n_words * pct_eng_long
    return valid_english, n_words, n_english


def correct_length(words, min_words, max_words, ignore_special_tokens=True):
    """Ensure text meets threshold for containing English words
    and that it's within the min and max words limits."""

    if min_words is None:
        min_words = 0

    if max_words is None:
        max_words = 99999

    n_words = 0
    for w in words:
        if punct_word(w):
            continue
        if ignore_special_tokens and is_special_token(w):
            continue
        n_words += 1
    valid = min_words <= n_words and n_words <= max_words
    return valid


def punct_word(word, punctuation=string.punctuation):
    return all([True if c in punctuation else False for c in word])


def load_non_english_user_set():
    non_english_user_set = set(np.load("uids.npz")["data"])
    return non_english_user_set


def non_english_user(userid, non_english_user_set):
    neu_found = int(userid) in non_english_user_set
    return neu_found


def separate_emojis_and_text(text):
    emoji_chars = []
    non_emoji_chars = []
    for c in text:
        if c in ALLOWED_EMOJIS:
            emoji_chars.append(c)
        else:
            non_emoji_chars.append(c)
    return "".join(emoji_chars), "".join(non_emoji_chars)


def extract_emojis(text, wanted_emojis):
    text = remove_variation_selectors(text)
    return [c for c in text if c in wanted_emojis]


def remove_variation_selectors(text):
    """Remove styling glyph variants for Unicode characters.
    For instance, remove skin color from emojis.
    """
    for var in VARIATION_SELECTORS:
        text = text.replace(var, "")
    return text


def shorten_word(word):
    """Shorten groupings of 3+ identical consecutive chars to 2, e.g. '!!!!' --> '!!'"""

    # only shorten ASCII words
    try:
        word.decode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError, AttributeError) as e:
        return word

    # must have at least 3 char to be shortened
    if len(word) < 3:
        return word

    # find groups of 3+ consecutive letters
    letter_groups = [list(g) for k, g in groupby(word)]
    triple_or_more = ["".join(g) for g in letter_groups if len(g) >= 3]
    if len(triple_or_more) == 0:
        return word

    # replace letters to find the short word
    short_word = word
    for trip in triple_or_more:
        short_word = short_word.replace(trip, trip[0] * 2)

    return short_word


def detect_special_tokens(word):
    try:
        int(word)
        word = SPECIAL_TOKENS[4]
    except ValueError:
        if AtMentionRegex.findall(word):
            word = SPECIAL_TOKENS[2]
        elif urlRegex.findall(word):
            word = SPECIAL_TOKENS[3]
    return word


def process_word(word):
    """Shortening and converting the word to a special token if relevant."""
    word = shorten_word(word)
    word = detect_special_tokens(word)
    return word


def remove_control_chars(text):
    return CONTROL_CHAR_REGEX.sub("", text)


def convert_nonbreaking_space(text):
    # ugly hack handling non-breaking space no matter how badly it's been encoded in the input
    for r in ["\\\\xc2", "\\xc2", "\xc2", "\\\\xa0", "\\xa0", "\xa0"]:
        text = text.replace(r, " ")
    return text


def convert_linebreaks(text):
    # ugly hack handling non-breaking space no matter how badly it's been encoded in the input
    # space around to ensure proper tokenization
    for r in ["\\\\n", "\\n", "\n", "\\\\r", "\\r", "\r", "<br>"]:
        text = text.replace(r, " " + SPECIAL_TOKENS[5] + " ")
    return text


# torchmoji/word_generator.py

""" Extracts lists of words from a given input to be used for later vocabulary
    generation or for creating tokenized datasets.
    Supports functionality for handling different file types and
    filtering/processing of this input.
"""

try:
    unicode  # Python 2
except NameError:
    unicode = str  # Python 3

# Only catch retweets in the beginning of the tweet as those are the
# automatically added ones.
# We do not want to remove tweets like "Omg.. please RT this!!"
RETWEETS_RE = re.compile(r"^[rR][tT]")

# Use fast and less precise regex for removing tweets with URLs
# It doesn't matter too much if a few tweets with URL's make it through
URLS_RE = re.compile(r"https?://|www\.")

MENTION_RE = re.compile(RE_MENTION)
ALLOWED_CONVERTED_UNICODE_PUNCTUATION = """!"#$'()+,-.:;<=>?@`~"""


class WordGenerator:
    """Cleanses input and converts into words. Needs all sentences to be in
        Unicode format. Has subclasses that read sentences differently based on
        file type.

    Takes a generator as input. This can be from e.g. a file.
    unicode_handling in ['ignore_sentence', 'convert_punctuation', 'allow']
    unicode_handling in ['ignore_emoji', 'ignore_sentence', 'allow']
    """

    def __init__(
        self,
        stream,
        allow_unicode_text=False,
        ignore_emojis=True,
        remove_variation_selectors=True,
        break_replacement=True,
    ):
        self.stream = stream
        self.allow_unicode_text = allow_unicode_text
        self.remove_variation_selectors = remove_variation_selectors
        self.ignore_emojis = ignore_emojis
        self.break_replacement = break_replacement
        self.reset_stats()

    def get_words(self, sentence):
        """Tokenizes a sentence into individual words.
        Converts Unicode punctuation into ASCII if that option is set.
        Ignores sentences with Unicode if that option is set.
        Returns an empty list of words if the sentence has Unicode and
        that is not allowed.
        """

        if not isinstance(sentence, unicode):
            raise ValueError("All sentences should be Unicode-encoded!")
        sentence = sentence.strip().lower()

        if self.break_replacement:
            sentence = convert_linebreaks(sentence)

        if self.remove_variation_selectors:
            sentence = remove_variation_selectors(sentence)

        # Split into words using simple whitespace splitting and convert
        # Unicode. This is done to prevent word splitting issues with
        # twokenize and Unicode
        words = sentence.split()
        converted_words = []
        for w in words:
            accept_sentence, c_w = self.convert_unicode_word(w)
            # Unicode word detected and not allowed
            if not accept_sentence:
                return []
            else:
                converted_words.append(c_w)
        sentence = " ".join(converted_words)

        words = tokenize(sentence)
        words = [process_word(w) for w in words]
        return words

    def check_ascii(self, word):
        """Returns whether a word is ASCII"""

        try:
            word.decode("ascii")
            return True
        except (UnicodeDecodeError, UnicodeEncodeError, AttributeError):
            return False

    def convert_unicode_punctuation(self, word):
        word_converted_punct = []
        for c in word:
            decoded_c = unidecode(c).lower()
            if len(decoded_c) == 0:
                # Cannot decode to anything reasonable
                word_converted_punct.append(c)
            else:
                # Check if all punctuation and therefore fine
                # to include unidecoded version
                allowed_punct = punct_word(
                    decoded_c, punctuation=ALLOWED_CONVERTED_UNICODE_PUNCTUATION
                )

                if allowed_punct:
                    word_converted_punct.append(decoded_c)
                else:
                    word_converted_punct.append(c)
        return "".join(word_converted_punct)

    def convert_unicode_word(self, word):
        """Converts Unicode words to ASCII using unidecode. If Unicode is not
        allowed (set as a variable during initialization), then only
        punctuation that can be converted to ASCII will be allowed.
        """
        if self.check_ascii(word):
            return True, word

        # First we ensure that the Unicode is normalized so it's
        # always a single character.
        word = unicodedata.normalize("NFKC", word)

        # Convert Unicode punctuation to ASCII equivalent. We want
        # e.g. "\u203c" (double exclamation mark) to be treated the same
        # as "!!" no matter if we allow other Unicode characters or not.
        word = self.convert_unicode_punctuation(word)

        if self.ignore_emojis:
            _, word = separate_emojis_and_text(word)

        # If conversion of punctuation and removal of emojis took care
        # of all the Unicode or if we allow Unicode then everything is fine
        if self.check_ascii(word) or self.allow_unicode_text:
            return True, word
        else:
            # Sometimes we might want to simply ignore Unicode sentences
            # (e.g. for vocabulary creation). This is another way to prevent
            # "polution" of strange Unicode tokens from low quality datasets
            return False, ""

    def data_preprocess_filtering(self, line, iter_i):
        """To be overridden with specific preprocessing/filtering behavior
        if desired.

        Returns a boolean of whether the line should be accepted and the
        preprocessed text.

        Runs prior to tokenization.
        """
        return True, line, {}

    def data_postprocess_filtering(self, words, iter_i):
        """To be overridden with specific postprocessing/filtering behavior
        if desired.

        Returns a boolean of whether the line should be accepted and the
        postprocessed text.

        Runs after tokenization.
        """
        return True, words, {}

    def extract_valid_sentence_words(self, line):
        """Line may either a string of a list of strings depending on how
        the stream is being parsed.
        Domain-specific processing and filtering can be done both prior to
        and after tokenization.
        Custom information about the line can be extracted during the
        processing phases and returned as a dict.
        """

        info = {}

        pre_valid, pre_line, pre_info = self.data_preprocess_filtering(
            line, self.stats["total"]
        )
        info.update(pre_info)
        if not pre_valid:
            self.stats["pretokenization_filtered"] += 1
            return False, [], info

        words = self.get_words(pre_line)
        if len(words) == 0:
            self.stats["unicode_filtered"] += 1
            return False, [], info

        post_valid, post_words, post_info = self.data_postprocess_filtering(
            words, self.stats["total"]
        )
        info.update(post_info)
        if not post_valid:
            self.stats["posttokenization_filtered"] += 1
        return post_valid, post_words, info

    def generate_array_from_input(self):
        sentences = []
        for words in self:
            sentences.append(words)
        return sentences

    def reset_stats(self):
        self.stats = {
            "pretokenization_filtered": 0,
            "unicode_filtered": 0,
            "posttokenization_filtered": 0,
            "total": 0,
            "valid": 0,
        }

    def __iter__(self):
        if self.stream is None:
            raise ValueError("Stream should be set before iterating over it!")

        for line in self.stream:
            valid, words, info = self.extract_valid_sentence_words(line)

            # Words may be filtered away due to unidecode etc.
            # In that case the words should not be passed on.
            if valid and len(words):
                self.stats["valid"] += 1
                yield words, info

            self.stats["total"] += 1


class TweetWordGenerator(WordGenerator):
    """Returns np array or generator of ASCII sentences for given tweet input.
    Any file opening/closing should be handled outside of this class.
    """

    def __init__(
        self,
        stream,
        wanted_emojis=None,
        english_words=None,
        non_english_user_set=None,
        allow_unicode_text=False,
        ignore_retweets=True,
        ignore_url_tweets=True,
        ignore_mention_tweets=False,
    ):

        self.wanted_emojis = wanted_emojis
        self.english_words = english_words
        self.non_english_user_set = non_english_user_set
        self.ignore_retweets = ignore_retweets
        self.ignore_url_tweets = ignore_url_tweets
        self.ignore_mention_tweets = ignore_mention_tweets
        WordGenerator.__init__(self, stream, allow_unicode_text=allow_unicode_text)

    def validated_tweet(self, data):
        """A bunch of checks to determine whether the tweet is valid.
        Also returns emojis contained by the tweet.
        """

        # Ordering of validations is important for speed
        # If it passes all checks, then the tweet is validated for usage

        # Skips incomplete tweets
        if len(data) <= 9:
            return False, []

        text = data[9]

        if self.ignore_retweets and RETWEETS_RE.search(text):
            return False, []

        if self.ignore_url_tweets and URLS_RE.search(text):
            return False, []

        if self.ignore_mention_tweets and MENTION_RE.search(text):
            return False, []

        if self.wanted_emojis is not None:
            uniq_emojis = np.unique(extract_emojis(text, self.wanted_emojis))
            if len(uniq_emojis) == 0:
                return False, []
        else:
            uniq_emojis = []

        if self.non_english_user_set is not None and non_english_user(
            data[1], self.non_english_user_set
        ):
            return False, []
        return True, uniq_emojis

    def data_preprocess_filtering(self, line, iter_i):
        fields = line.strip().split("\t")
        valid, emojis = self.validated_tweet(fields)
        text = (
            fields[9].replace("\\n", "").replace("\\r", "").replace("&amp", "&")
            if valid
            else ""
        )
        return valid, text, {"emojis": emojis}

    def data_postprocess_filtering(self, words, iter_i):
        valid_length = correct_length(words, 1, None)
        valid_english, n_words, n_english = mostly_english(words, self.english_words)
        if valid_length and valid_english:
            return (
                True,
                words,
                {
                    "length": len(words),
                    "n_normal_words": n_words,
                    "n_english": n_english,
                },
            )
        else:
            return (
                False,
                [],
                {
                    "length": len(words),
                    "n_normal_words": n_words,
                    "n_english": n_english,
                },
            )


from typing import List


class TorchMojiInterface:
    def __init__(self, vocabulary_file: str, model_path: str, maxlen: int = 30):
        with open(vocabulary_file, "r") as f:
            self.vocabulary = json.load(f)
        self.st = SentenceTokenizer(self.vocabulary, maxlen)
        self.emoji_model = torchmoji_emojis(model_path)
        self.feature_model = torchmoji_feature_encoding(model_path)

    def top_elements(self, array, k):
        ind = np.argpartition(array, -k)[-k:]
        return ind[np.argsort(array[ind])][::-1]

    def top_n_emojis(self, text: List[str], n_emojis: int = 5):
        """
        Returns the top n emojis in the form [":joy:",":unamused:"]
        """
        tokenized, _, _ = self.st.tokenize_sentences(text)
        predicted_probs = self.emoji_model(tokenized)
        print(predicted_probs.shape)
        emojis = []
        for probs in predicted_probs:
            emoji_ids = self.top_elements(probs, n_emojis)
            emojis.append(list(map(lambda x: EMOJIS[x], emoji_ids)))
        return emojis

    def encode_texts(self, text: List[str]):
        """
        Returns the encoded embedding for the text input
        Output shape: [len(text),2304]
        """
        tokenized, _, _ = self.st.tokenize_sentences(text)
        encoding = self.feature_model(tokenized)
        return encoding

    def blend_text_encodings(self, texts: List[str], weights: List[float]):
        """
        Computes encodings and blends them
        """
        encodings = self.encode_texts(texts)
        return self.blend_encodings(encodings, weights)

    def blend_encodings(self, encodings, weights):
        """
        Compute weighted average of encodings
        """
        return np.average(encodings, axis=0, weights=weights)

    def enc2emojis(self, encodings, n_emojis=5):
        predicted_probs = self.emoji_model.output_layer(encodings).detach().numpy()
        print(predicted_probs.shape)
        emojis = []
        for probs in predicted_probs:
            emoji_ids = self.top_elements(probs, n_emojis)
            emojis.append(list(map(lambda x: EMOJIS[x], emoji_ids)))
        return emojis
