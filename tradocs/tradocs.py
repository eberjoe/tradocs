import requests
import os
import shutil
import re
import codecs
import time
import datetime
import click
import json
from git import Repo
from colorama import init
from pathlib import Path

targetPaths = []
stats = []
cont = ''
greenFlag = False
processed = False
reqs = 0
chars = 0
enUi = ['button', 'checkbox', 'field', 'column', 'area', 'box', 'role', 'user', 'line', 'table', 'mode', 'module', 'menu', 'event',
        'RFx', 'search', 'page', 'tab', 'panel', 'option', 'dialog', 'status', 'tag', 'symbol', 'sign', 'label', 'scenario', 'link',
        'auction', 'events', 'checkboxes', 'columns', 'lines', 'answers', 'answer', 'responses', 'response', 'buttons', 'fields',
        'tabs', 'icon', 'icons', 'users', 'widget', 'widgets', 'window', 'windows', 'dialog box', 'dialog boxes', 'modal window',
        'modal windows', 'dialog window', 'dialog windows', 'homepage', 'folder', 'folders', 'file', 'files', 'project', 'projects',
        'image', 'images']

# Configuração da API de tradução

urlTrad = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
apiTradKey = ''

# Idioma fonte

sourceLang = ''

# Idiomas traduzidos

targetLangs = []

# Diretório fonte

sourceDir = ''

# Configurações

configs = {}

# Preservação da sintaxe Markdown DocFX

mdRegex = re.compile(r'''(\]\(.+?\)[\W ]?)|          # referência de imagem ou link
                         (uid:\s?[\w.]+)|            # âncora de link no cabeçalho
                         (\{\{.*?\}\}[\W ]+?)|       # nome de elemento de UI
                         (:{3}\s*[a-z]*)|            # demarcador de bloco de ênfase customizado para o Docs 2.0
                         (`{1,3}.+?`{1,3}[\W ]?)|    # bloco de código
                         (<.+?>)|                    # HTML
                         ([-=|_:]{2,})|              # linha horizontal e divisor de cabeçalho de tabela
                         (\s*?\d\.\s)|               # numeração em lista numerada
                         (\s?[\[!#*|>\r\n\t]+?\s*)   # outros elementos de Markdown DocFX''', re.VERBOSE | re.DOTALL)

# Preservação da sintaxe Yaml DocFX

ymlRegex = re.compile(r'(name: [ \w\'\-]+)')         # traduz texto entre 'name: ' e quebra de linha

#--------------------------------

def ProcessFiles(sourceFile):
    fileName = sourceFile.split('/')[-1]
    if fileName[-3:] in ('yml', '.md'):
        file = codecs.open(sourceFile, encoding = 'utf-8', mode = 'r')
        sourceContent = (file.read())
        file.close()
        PrLightPurple('\n ' + sourceFile)
        for i in range (len(targetLangs)):
            langCombo = sourceLang + '-' + targetLangs[i]
            targetContent = ''
            if fileName[-3:] == 'yml':
                PrGreen('\n Traslating Yaml from ' + sourceLang + ' to ' + targetLangs[i])
                slicedApple = list(filter(lambda x: x != '' and x is not None, ymlRegex.split(sourceContent)))
                for piece in slicedApple:
                    if not ymlRegex.fullmatch(piece):
                        targetContent += piece
                    else:
                        localized = 'name: ' + Translate(piece[6:], langCombo).title()
                        targetContent += localized
            else:
                PrGreen('\n Traslating Markdown from ' + sourceLang + ' to ' + targetLangs[i])
                if sourceLang[:2] == 'en':
                    slicedUi = re.split(r'(\{\{.*?\}\} [a-zA-Z]+)', sourceContent)
                    for j in range(len(slicedUi)):
                        if re.fullmatch(r'\{\{.*?\}\} [a-zA-Z]+', slicedUi[j]) and re.search(r'(?<=\}\} ).+', slicedUi[j]).group().casefold() in enUi:
                            slicedUi[j] = ' '.join(re.split(r'(?<=\}\}) ', slicedUi[j])[::-1])
                    sourceContent = ''.join(slicedUi)
                    slicedItalic = re.split(r'(\*.*?\* [a-zA-Z]+)', sourceContent)
                    for j in range(len(slicedItalic)):
                        if re.fullmatch(r'\*.*?\* [a-zA-Z]+', slicedItalic[j]) and re.search(r'(?<=\* ).+', slicedItalic[j]).group().casefold() in enUi:
                            slicedItalic[j] = ' '.join(re.split(r'(?<=\*) ', slicedItalic[j])[::-1])
                    sourceContent = ''.join(slicedItalic)
                    slicedBold = re.split(r'(\*\*.*?\*\* [a-zA-Z]+)', sourceContent)
                    for j in range(len(slicedBold)):
                        if re.fullmatch(r'\*\*.*?\*\* [a-zA-Z]+', slicedBold[j]) and re.search(r'(?<=\*\* ).+', slicedBold[j]).group().casefold() in enUi:
                            slicedBold[j] = ' '.join(re.split(r'(?<=\*\*) ', slicedBold[j])[::-1])
                    sourceContent = ''.join(slicedBold)
                slicedApple = list(filter(lambda x: x != '' and x is not None, mdRegex.split(sourceContent)))
                for piece in slicedApple:
                    if mdRegex.fullmatch(piece):
                        if re.fullmatch(r'\]\(#.+\)', piece):
                            anchor = Translate(' '.join(piece[3:-1].split('-')), langCombo)
                            targetContent += '](#' + '-'.join(anchor.split(' ')).lower() + ')'
                        else:
                            targetContent += piece
                    else:
                        localized = Translate(piece, langCombo)
                        if type(localized) is list:
                            localized = localized[0]
                        targetContent += localized
            file = codecs.open(targetPaths[i] + '/' + '/'.join(sourceFile.split('/')[1:]), encoding = 'utf-8', mode = 'w+')
            file.write(targetContent)
            file.close()
        return

    PrLightPurple('Copying ' + sourceFile)
    for i in range (len(targetLangs)):
        shutil.copy(sourceFile, targetPaths[i] + '/' + '/'.join(sourceFile.split('/')[1:]))

#--------------------------------

def FileStats(sourceFile):
    fileName = sourceFile.split('/')[-1]
    if fileName[-3:] not in ('yml', '.md'): return
    file = codecs.open(sourceFile, encoding = 'utf-8', mode = 'r')
    content = (file.read())
    file.close()
    charsFile = 0
    reqsFile = 0
    if fileName[-3:] == 'yml':
        reqsFile = len(ymlRegex.findall(content))
        charsFile = len(''.join(ymlRegex.findall(content)))
    else:
        slicedApple = list(filter(lambda x: x != '' and x is not None, mdRegex.split(content)))
        for d in slicedApple:
            if mdRegex.fullmatch(d) is None:
                reqsFile += 1
                charsFile += len(d)
    return [reqsFile * len(targetLangs), charsFile]

#--------------------------------

def Translate(text, langCombo):
    if re.search(r'\w', text) is None: return [text for n in targetLangs]
    firstLetter = re.search(r'\w', text).group()
    resp = requests.get(
        urlTrad,
        params = {
            'key': apiTradKey,
            'lang': langCombo,
            'text': text
            }
    )
    print(resp.status_code)
    if resp.status_code != 200:
        PrRed('Translation failed!')
        exit()
    translation = resp.json()['text'][0]
    try:
        firstLetterTranslated = re.search(r'\w', translation).group()
    except:
        firstLetterTranslated = ''
    if firstLetter.islower():
        translation = re.sub(r'\w', firstLetterTranslated.lower(), translation, count = 1)
    print(translation + '\n')
    return translation

#--------------------------------
    
def PrRed(skk):
    print('\033[91m {}\033[00m'.format(skk))

def PrYellow(skk):
    print('\033[93m {}\033[00m'.format(skk))

def PrGreen(skk):
    print('\033[92m {}\033[00m'.format(skk))

def PrLightPurple(skk):
    print('\033[94m {}\033[00m'.format(skk))

#--------------------------------

def RepoCheck():
    if sourceDir not in os.listdir():
        PrRed('\nThe directory "' + sourceDir + '" for source files has not been found!')
        exit()

    for lang in targetLangs:
        targetPaths.append('_'.join(lang.split('-')).lower())

    try:
        repo = Repo()
    except:
        PrRed("You aren't in a repository!\n Initialize a Git repo and make the first commit.")
        re.purge
        exit()
    modifiedUnstaged = repo.index.diff(None)

    try:
        modifiedStaged = repo.index.diff('HEAD')
    except:
        PrRed("HEAD could not be found!\n Please make the first commit.")
        re.purge
        exit()

    allModified = modifiedStaged + modifiedUnstaged
    untrackedSrc = [n for n in repo.untracked_files if n.split('/')[1:] in os.listdir(sourceDir)]
    return [n.a_blob.path for n in allModified if n.a_blob.path.split('/')[0] == '_'.join(sourceLang.split('-')).lower()] + untrackedSrc

#--------------------------------

@click.group()
def root():
    """Traslation of DocFX source code"""
    global apiTradKey
    global sourceLang
    global targetLangs
    global sourceDir
    global configs
    init()
    try:
        with open(os.path.expanduser('~') + '/' + 'tradocs.config.json', 'r') as file:
            configs = json.load(file)
        apiTradKey = configs['TRANSLATOR_KEY']
        sourceLang = configs['SOURCE']
        targetLangs = configs['TARGET']
    except:
        print(" Hey firstcomer, welcome to Tradocs!\n Please set up a few things before proceeding...")
        apiTradKey = input(' Please enter your Yandex.Translate API key: ')
        sourceLang = input(' Enter the ISO 639-1 (two-letter code) identifier for the source language: ').lower()
        targetLangs = input(' Enter the ISO 639-1 identifiers for the target languages, separated by space: ').lower().split(' ')
        configs = {
            'TRANSLATOR_KEY': apiTradKey,
            'SOURCE': sourceLang,
            'TARGET': targetLangs
        }
        with open(os.path.expanduser('~') + '/' + 'tradocs.config.json', 'w+') as file:
            json.dump(configs, file)
    sourceDir = '_'.join(sourceLang.split('-')).lower()

@root.command()
@click.option('-k', '--api-key', type=str)
@click.option('-s', '--source', type=str)
@click.option('-t', '--target', type=str)
def config(api_key, source, target):
    global configs
    """Show and set configuration"""
    if not (api_key or source or target):
        print(' Source language:\t' + configs['SOURCE'])
        print(' Target languages:\t' + ' '.join(configs['TARGET']))
        print(' Yandex API key:\t' + configs['TRANSLATOR_KEY'])
        exit()
    if api_key: configs['TRANSLATOR_KEY'] = api_key
    if source: configs['SOURCE'] = source
    if target: configs['TARGET'] = target.split(' ')
    with open(os.path.expanduser('~') + '/' + 'tradocs.config.json', 'w+') as file:
        json.dump(configs, file)
    re.purge
    exit()

@root.command()
def diff():
    """Translation of modified files (work tree)"""
    global reqs
    global chars
    global cont
    workTree = RepoCheck()
    if workTree:
        PrYellow('\n The following files will be added or overwritten in target languages:')
        for doc in workTree:
            if doc.split('/')[-1] in os.listdir(sourceDir + '/' + '/'.join(doc.split('/')[1:-1])):
                stats.append(FileStats(doc))
                PrLightPurple(doc)
            else:
                PrYellow(doc + ' will be deleted in target languages.')
        fls = list(filter(lambda x: x is not None, stats))
        for i in range(len(fls)):
            reqs += fls[i][0]
            chars += fls[i][1]
        estimatedT = int(reqs*1.1)
        print('\n Target languages:\t\t\t' + ', '.join(targetLangs))
        print(' Total of calls to translation service:\t' + str(reqs))
        print(' Total of characters for translation:\t' + str(chars * len(targetLangs)))
        print(' Estimated process duration:\t\t' + str(datetime.timedelta(seconds = estimatedT)))
        cont = input('\n Continue [c] or abort [Enter]? ')
        if cont == 'c':
            for doc in workTree:
                if doc.split('/')[-1] in os.listdir(sourceDir + '/' + '/'.join(doc.split('/')[1:-1])):
                    ProcessFiles(doc)
                else:
                    for path in targetPaths:
                        try:
                            os.remove(path + '/' + '/'.join(doc.split('/')[1:]))
                        except:
                            pass
            PrGreen('\n Completed successfully!')
    else:
        PrYellow('There have been no changes to the source language directory since the last commit.')
    if cont != 'c': PrRed('\n Exiting...')
    time.sleep(1)
    re.purge
    exit()

@root.command()
def all():
    """Translation of the entire DocFX project"""
    global processed
    global greenFlag
    global reqs
    global chars
    RepoCheck()
    while not processed:
        if greenFlag:
            for item in Path().iterdir():
                if item.name != sourceDir and item.name in list(map(lambda x: '_'.join(x.split('-')).lower(), targetLangs)) and item.is_dir():
                    shutil.rmtree(item.name)
            processed = True
        if greenFlag:
            for path in targetPaths:
                os.mkdir(path)
        for entry in Path(sourceDir).iterdir():
            if entry.is_dir():
                dirLevel2 = sourceDir + '/' + entry.name
                if greenFlag:
                    for path in targetPaths:
                        os.mkdir(path + '/' + entry.name)
                for entry2 in Path(dirLevel2).iterdir():
                    if entry2.is_dir():
                        tgSeg = '/' + entry.name + '/' + entry2.name
                        dirLevel3 = dirLevel2 + '/' + entry2.name
                        if greenFlag:
                            for path in targetPaths:
                                os.mkdir(path + tgSeg)
                        for entry3 in Path(dirLevel3).iterdir():
                            if entry3.is_dir():
                                tgSeg = '/' + entry.name + '/' + entry2.name + '/' + entry3.name
                                dirLevel4 = dirLevel3 + '/' + entry3.name
                                if greenFlag:
                                    for path in targetPaths:
                                        os.mkdir(path + tgSeg)
                                for entry4 in Path(dirLevel4).iterdir():
                                    if entry4.is_dir():
                                        tgSeg = '/' + entry.name + '/' + entry2.name + '/' + entry3.name + '/' + entry4.name
                                        dirLevel5 = dirLevel4 + '/' + entry4.name
                                        if greenFlag:
                                            for path in targetPaths:
                                                os.mkdir(path + tgSeg)
                                        for entry5 in Path(dirLevel5).iterdir():
                                            if not entry5.is_dir():
                                                if greenFlag:
                                                    ProcessFiles(dirLevel5 + '/' + entry5.name)
                                                else:
                                                    stats.append(FileStats(dirLevel5 + '/' + entry5.name))
                                    else:
                                        if greenFlag:
                                            ProcessFiles(dirLevel4 + '/' + entry4.name)
                                        else:
                                            stats.append(FileStats(dirLevel4 + '/' + entry4.name))
                            else:
                                if greenFlag:
                                    ProcessFiles(dirLevel3 + '/' + entry3.name)
                                else:
                                    stats.append(FileStats(dirLevel3 + '/' + entry3.name))
                    else:
                        if greenFlag:
                            ProcessFiles(dirLevel2 + '/' + entry2.name)
                        else:
                            stats.append(FileStats(dirLevel2 + '/' + entry2.name))
            else:
                if greenFlag:
                    ProcessFiles(sourceDir + '/' + entry.name)
                else:
                    stats.append(FileStats(sourceDir + '/' + entry.name))
        if not greenFlag:
            fls = list(filter(lambda x: x is not None, stats))
            nFls = len(fls)*len(targetLangs)
            print('\n Target languages:\t\t\t' + ', '.join(targetLangs))
            print(' Total of source language files:\t' + str(len(fls)))
            for i in range(len(fls)):
                reqs += fls[i][0]
                chars += fls[i][1]
            estimatedT = int(reqs*1.1)
            print(' Total of source language characters:\t' + str(chars))
            print(' Total of files to be generated:\t' + str(nFls))
            print(' Total of calls to translation service:\t' + str(reqs))
            print(' Total of characters for translation:\t' + str(chars * len(targetLangs)))
            print(' Estimated process duration:\t\t' + str(datetime.timedelta(seconds = estimatedT)))
            cont = input('\n Continue [c] or abort [Enter]? ')
            if cont == 'c':
                greenFlag = True
            else:
                break
    if greenFlag:
        PrGreen('\n Completed successfully!')
    else:
        PrRed('\n Exiting...')
    time.sleep(1)
    re.purge()
    exit()
