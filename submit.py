import os
import sys


def run(commit_message):
    os.system('git add source')
    os.system('git commit -m "%s"' % commit_message)
    os.system('git push origin hexo-backup')

    os.system('hexo clean')
    os.system('hexo d -g')


if __name__ == '__main__':
    msg = sys.argv[1]
    run(msg)
