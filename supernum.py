#!/bin/python

"""
  Supernum is a pragmatic static site generator using jinja2 templates,
  reStructeredText or Markdown.

  Usage:
    supernum [-fh] [<workdir>] [-c <context>] [-t <templates>] [-i <index>] [-r <root>] [-b <build>]

  Options:
    <workdir>       Directory where the source files can be found. Defaults to the
                    current working directory.
    -c <context>    Filename of the main context file. Defaults to context.yaml.
    -t <templates>  Filename of the directory containing the template files.
                    Defaults to templates.
    -i <index>      Filename of the directory index file. Defaults to
                    index.html.
    -r <root>       Name of the folder containing the document root. Defaults to
                    root.
    -b <build>      Name of the ouput folder. Defaults to build.
    -f              Delete all contents of the build folder if exists without
                    asking.
    -h              Print this text.

"""

import os
import sys
from docopt import docopt
from clint.textui import colored, puts, indent
import yaml
import shutil
import markdown
from docutils.core import publish_parts
from jinja2 import Environment, PackageLoader, FileSystemLoader
from copy import deepcopy


class Supernum(object):

    decoders = {
        'rst': lambda x: publish_parts(x, writer_name='html')['html_body'],
        'md': lambda x: markdown.markdown(x),
    }

    def __init__(self, context='context.yaml', templates='templates',
        index='index.html', root='root', build='build', force=False):

        self.index = index
        self.root_dir = root
        self.build_dir = build
        self.force = force

        # Create Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(templates))
    
        # Load base context
        fd = open(context, 'rb')
        self.context = yaml.load(fd.read())
        fd.close()

        if self.context is None:
            self.context = {}

    def read(self, path):
        fd = open(path, 'rb')
        content = fd.read()
        fd.close()

        return content

    def write(self, path, content):
        fd = open(path, 'wb')
        fd.write(content)
        fd.close()

    def makedir(self, path):
        if os.path.exists(path):
            if not self.force:
                self.force = raw_input(path + ' exists. Contents will be deleted. Continue [yes/no]? ') == 'yes'
            if not self.force:
                sys.exit(0)

            shutil.rmtree(path)

        os.makedirs(path)

    def split_content(self, content):
        index = content.find('\n\n')
        meta = yaml.load(content[:index])
        content = content[index:]

        return (meta, content)

    def render(self, content, decoder):
        meta, content = self.split_content(content)

        context = deepcopy(self.context)
        context.update(meta)

        template  = "{% extends 'base.html' %}\n"
        template += '\n'
        template += '{% block content %}\n'
        template += decoder(content)
        template += '{% endblock %}'

        return self.env.from_string(template).render(context).encode('utf-8')

    def fabricate(self, src, dst):
        with indent(3, quote=colored.green('>> ')):
            puts(dst)

        fd = file(src, 'rb')
        content = fd.read()
        fd.close()

        for ending, decoder in self.decoders.items():
            if ending == src.split('.')[-1]:
                content = self.render(content, decoder)
                dst = dst[:-len(ending)] + 'html'

        self.write(dst, content)

    def walk(self):
        for base, dirs, files in os.walk(self.root_dir):
            output = self.build_dir + base[len(self.root_dir):]

            for d in dirs:
                self.makedir(os.path.join(output, d))

            for f in files:
                src = os.path.join(base, f)
                dst = os.path.join(output, f)
                
                self.fabricate(src, dst)

    def build(self):
        self.makedir(self.build_dir)
        self.walk()


if __name__ == '__main__':
    args = docopt(__doc__)

    if args['<workdir>']:
        os.chdir(args['<workdir>'])

    kwargs = {}
    for key in ['context', 'templates', 'root', 'build']:
        try:
            v = args['<' + key + '>']
        except KeyError:
            pass
        else:
            kwargs[key] = v

    if args['-f']:
        kwargs['force'] = True

    snum = Supernum(**kwargs)
    snum.build()