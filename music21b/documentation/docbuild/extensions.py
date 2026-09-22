# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         extensions.py
# Purpose:      Sphinx extension for hiding and showing lines in docs
#
# Authors:      Josiah Wolf Oberholtzer
#
# Copyright:    Copyright © 2013-22 Michael Scott Asato Cuthbert
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
from __future__ import annotations

# loaded by source/conf.py

_DOC_IGNORE_MODULE_OR_PACKAGE = True


def fixLines(lines):
    newLines = []
    include = True
    for line in lines:
        if ' #_DOCS_SHOW ' in line:
            if include:
                newLines.append(line.replace(' #_DOCS_SHOW ', ' '))
        elif '# _DOCS_SHOW' in line:
            if include:
                newLines.append(line.replace('# _DOCS_SHOW', ' '))
        elif 'OMIT_FROM_DOCS' in line:
            include = False
        elif 'RESUME_DOCS' in line:
            include = True
        elif '#_RAISES_ERROR' in line:
            newLines.append(line.replace(' #_RAISES_ERROR', ' '))
        elif include:
            newLines.append(line)
    lines[:] = newLines

def processDocstring(app, what, name, obj, options, lines):
    '''
    Process the ``lines`` of each docstring, in place.
    '''
    #    print('WHAT ', what)
    #    print('NAME ', name)
    #    print('OBJ  ', obj)
    #    print('OPTS ', options)
    #    print('LINES', lines)
    fixLines(lines)


def processSource(app, name, lines):
    linesSep = lines[0].split('\n')
    fixLines(linesSep)
    lines[0] = '\n'.join(linesSep)


def setup(app):
    app.connect('autodoc-process-docstring', processDocstring)
    app.connect('source-read', processSource)
    extension_metadata = {'version': '1.0',
                          'parallel_read_safe': True,
                          'parallel_write_safe': True,
                          }
    return extension_metadata
