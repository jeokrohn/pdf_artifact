#!/usr/bin/env python
"""
Playing with pikepdf to try to remove artifacts from PDFs
pikepdf requires qpdf to be installed:
    https://medium.com/@jeremie.lumbroso/installing-pikepdf-with-homebrew-on-macos-big-sur-2a21995d0cfe
"""
import os
import sys
from typing import Iterable, Generator, Iterator

from pikepdf import Pdf, parse_content_stream, unparse_content_stream
from pikepdf.models import UnparseableContentStreamInstructions


def skip_until_emc(*, stream: Iterator[UnparseableContentStreamInstructions]):
    """
    Skip stream until EMC operator
    :param stream:
    :return:
    """
    for arguments, operator in stream:
        str_op = str(operator)
        if str_op == 'EMC':
            # we are done
            break
        if str_op in ['BMC', 'BDC']:
            # skip until nested EMC
            skip_until_emc(stream=stream)


def filter_artifact(*, stream: Iterable[UnparseableContentStreamInstructions]) -> \
        Generator[UnparseableContentStreamInstructions, None, None]:
    """
    Filter /Artifact BMC ... EMC from stream
    :param stream:
    :return:
    """
    stream_iter = iter(stream)
    for arguments, operator in stream_iter:
        if str(operator) == 'BMC' and arguments and str(arguments[0]) == '/Artifact':
            # skip until operator 'EMC'
            skip_until_emc(stream=stream_iter)
            continue
        yield arguments, operator


def process_one_pdf(path: str):
    """
    Process a single PDF and save a _filtered version
    :param path:
    :return:
    """
    print()
    print(path)
    target = os.path.abspath(path)
    print(f'->{target}')

    pdf = Pdf.open(target)

    for page in pdf.pages:
        stream = parse_content_stream(page)
        new_stream = unparse_content_stream(list(filter_artifact(stream=stream)))
        page.Contents = pdf.make_stream(new_stream)

    modified_path = f'{os.path.splitext(target)[0]}_filtered.pdf'
    pdf.save(modified_path)


def main():
    args = sys.argv
    if len(args) == 1:
        print('Missing arguments', file=sys.stderr)
        exit(1)
    for path in args[1:]:
        process_one_pdf(path=path)
    exit(0)


if __name__ == '__main__':
    main()
