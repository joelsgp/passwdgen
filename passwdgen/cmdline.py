# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import sys
from getpass import getpass
import argparse

from generator import *
from utils import *
from constants import *


def show_password_entropy(passwd, word_list):
    """Displays the password entropy calculation results."""
    entropy = calculate_entropy(passwd, dict_set=word_list)
    print("\nPassword length: %d characters" % len(passwd))
    print("\nEntropy")
    print("-------")
    for charset, charset_name in list(PASSWORD_CHARSET_NAMES):
        print(("{:<%d}" % LONGEST_CHARSET_NAME_LEN).format(charset_name) + " : " +
              (("%.6f" % entropy[charset]) if charset in entropy else "not in character set"))
    print("")


def main():
    """Main routine for handling command line functionality for passwdgen."""

    parser = argparse.ArgumentParser(description="A password generation utility.")
    subparsers = parser.add_subparsers(help="The command to execute.", dest="command")

    parser_info = subparsers.add_parser(
        "info",
        help=(
            "Compute information about one or more passwords. If no password file is specified, it attempts to " +
            "read a password from stdin."
        )
    )
    parser_info.add_argument(
        "-d", "--dictionary",
        default=None,
        help="Path to the dictionary file to use. This must be a plain text file with one word per line."
    )
    parser_info.add_argument(
        "--password_file",
        default=None,
        help=(
            "Read passwords from a file instead of the command line (assumes a text file, one password per line, " +
            "skips newlines)."
        )
    )
    parser_info.add_argument(
        "-e", "--encoding",
        default=None,
        help=(
            "The encoding to use when read/writing input/output files. " +
            "(See https://docs.python.org/2/library/codecs.html#standard-encodings)"
        )
    )

    parser_generate = subparsers.add_parser(
        "generate",
        help="Generate password(s)."
    )
    parser_generate.add_argument(
        "--charset",
        choices=PASSWORD_CHARSET_IDS,
        default=PC_DICT,
        help=(
            "Which character set/approach to use when generating the password (default=\"%s\"). See the " +
            "README.md file at https://github.com/thanethomson/passwdgen for more details."
        ) % PC_DICT
    )
    parser_generate.add_argument(
        "-c", "--clipboard",
        action="store_true",
        help=(
            "Copy the generated password to the clipboard (only for when generating a single password) instead of "+
            "writing the password to stdout"
        )
    )
    parser_generate.add_argument(
        "-d", "--dictionary",
        default=None,
        help="Path to the dictionary file to use. This must be a plain text file with one word per line."
    )
    parser_generate.add_argument(
        "-e", "--encoding",
        default=None,
        help=(
            "The encoding to use when read/writing input/output files. " +
            "(See https://docs.python.org/2/library/codecs.html#standard-encodings)"
        )
    )
    parser_generate.add_argument(
        "-i", "--info",
        action="store_true",
        help="Additionally display information about the generated password, including password entropy."
    )
    parser_generate.add_argument(
        "-l", "--length",
        default=None,
        help=(
            "The default number of characters or words to generate, depending on which kind of password " +
            "is being generated (a character- or dictionary-based one). Defaults: %d characters or %d words."
        ) % (DEFAULT_CHAR_PASSWORD_LENGTH, DEFAULT_WORD_PASSWORD_WORDS)
    )
    parser_generate.add_argument(
        "-m", "--min-entropy",
        default=None,
        type=int,
        help="The minimum entropy of the required password (optional). If length is specified, this will be ignored."
    )
    parser_generate.add_argument(
        "-s", "--separator",
        choices=PASSWORD_SEPARATOR_IDS,
        default=SEP_DASH,
        help=(
            "The separator to use when generating passwords from dictionaries (default=%s)."
        ) % SEP_DASH
    )

    parser_rng = subparsers.add_parser(
        "rng",
        help="Test the quality of the operating system's random number generator."
    )
    parser_rng.add_argument(
        "-s", "--sample-size",
        type=int,
        default=1000000,
        help="Define the sample size to test with (default = 1,000,000)."
    )

    parser_wordlist = subparsers.add_parser(
        "wordlist",
        help="Utilities relating to word list manipulation."
    )
    subparsers_wordlist = parser_wordlist.add_subparsers(dest="wordlist_subcommand")

    parser_wordlist_clean = subparsers_wordlist.add_parser(
        "clean",
        help="Cleans up a given word list, stripping punctuation, digits and whitespace."
    )
    parser_wordlist_clean.add_argument(
        "input_file",
        help="The input text file, one word per line, to be cleaned."
    )
    parser_wordlist_clean.add_argument(
        "output_file",
        help="The output file into which to write the cleaned word list."
    )
    parser_wordlist_clean.add_argument(
        "-e", "--encoding",
        default=None,
        help=(
            "The encoding to use when read/writing input/output files. " +
            "(See https://docs.python.org/2/library/codecs.html#standard-encodings)"
        )
    )

    args = parser.parse_args()

    if args.command == "info":
        if args.password_file is None:
            if sys.stdin.isatty():
                passwd = getpass("Please enter the password to check: ")
            else:
                # if the input's been piped in
                passwd = sys.stdin.read()
                # strip off the single trailing newline
                if passwd.endswith("\n"):
                    passwd = passwd[:-1]

            word_list = load_word_list(filename=args.dictionary, encoding=args.encoding)
            show_password_entropy(passwd, word_list)

    elif args.command == "rng":
        print("Testing OS RNG. Attempting to generate %d samples between 0 and 100 (inclusive). Please wait..." % args.sample_size)
        result = secure_random_quality(args.sample_size)
        print("\nStatistics")
        print("----------")
        print("Mean               : %.6f (should approach 50.0 as the sample size increases)" % result['mean'])
        print("Standard deviation : %.6f (should be as close to 0.0 as possible)" % result['stddev'])
        print("Variance           : %.6f (should be as close to 0.0 as possible)" % result['variance'])
        print("Time taken         : %.3f seconds\n" % result['time'])

    elif args.command == "generate":
        word_list = load_word_list(filename=args.dictionary, encoding=args.encoding)

        # dictionary-based password generation
        if args.charset == PC_DICT:
            # load our dictionary
            passwd = generate_password_words(
                word_list,
                separator=PASSWORD_SEPARATORS[args.separator],
                word_count=args.length,
                min_entropy=args.min_entropy
            )
        else:
            passwd = generate_password_chars(
                args.charset,
                length=args.length,
                min_entropy=args.min_entropy
            )

        print(passwd)

        if args.info:
            show_password_entropy(passwd, word_list)

    elif args.command == "wordlist":
        if args.wordlist_subcommand == "clean":
            print("Attempting to clean word list: %s" % args.input_file)
            result = clean_word_list(
                args.input_file,
                args.output_file,
                encoding=args.encoding
            )
            print("Cleaned file in %.3f seconds. Read %d words, wrote %d." % (
                result["time"],
                result["words_read"],
                result["words_written"]
            ))