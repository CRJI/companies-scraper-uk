#!/usr/bin/env python3
import cmd
import sys

from companies_house import process_companies_house


class ScrapeCmd(cmd.Cmd):

    def do_companies_house(self, *args):
        process_companies_house()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        ScrapeCmd().onecmd(sys.argv[1])
