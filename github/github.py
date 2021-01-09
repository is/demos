import sys
import os
import re


from typing import List

class Github(object):
    def __init__(self, argv:List[str]):
        self.argv = argv
        self.git_argv:List[str] = None
        self.src_raw:str = None
        self.dst_raw:str = None
        self.src:str = None

        self.site:str = None
        self.group:str = None
        self.repo:str = None
        self.protocol:str = 'ssh'

        self.dst_path:str = None


    def command(self) -> bool:
        argv = self.argv
        if len(argv) <= 1:
            return False

        argv = argv[1:]
        while len(argv) > 0:
            arg = argv.pop(0)
            if arg == '--':
                self.git_argv = argv
                break

            if arg.startswith('-') or arg.startswith('+'):
                arg_opt = arg[1:]
                print(arg_opt)
                continue

            if self.src_raw == None:
                self.src_raw = arg
                continue

            if self.dst_raw == None:
                self.dst_raw = arg
                continue

            return False

        if self.src_raw == None:
            return False
        return True


    def usage(self) -> None:
        print("github [options] src [dst] [ -- {git options}]")


    def parse_source(self) -> None:
        src_raw = self.src_raw

        ## https://github.com/microsoft/vscode
        r0 = re.compile(r'''https://.+?/(.+?)/(.+?)$''')
        m = r0.match( src_raw)
        if m != None:
            self.site = 'github.com'
            self.group = m[1]
            self.repo = m[2]
            return


    def clone(self) -> None:
        base_path = os.path.dirname(self.dst_path)
        try:
            os.makedirs(base_path)
        except FileExistsError:
            pass

        if self.protocol == 'ssh':
            self.src = f'''git@{self.site}:{self.group}/{self.repo}.git'''

        git_opts = ''
        if self.git_argv != None:
            git_opts = ' '.join(self.git_argv)

        cmd = f'''git clone {git_opts}{self.src} {self.dst_path}'''
        if self.site == 'github.com':
            print(f'''== GITHUB == ''')
            print(f'''SRC: {self.src}''')
            print(f'''DEST: {self.dst_path}''')
            print(f'''CMD: {cmd}''')


    def run(self) -> None:
        if not self.command():
            self.usage()
            return

        self.parse_source()
        if self.site == None or self.repo == None or self.group == None:
            return

        if self.dst_raw == None:
            self.dst_path = os.path.join(
                os.environ['HOME'], 'src', self.site, self.group, self.repo)
        else:
            self.dst_path = self.dst_raw
        self.clone()


if __name__ == '__main__':
    Github(sys.argv).run()