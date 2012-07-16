#!/usr/bin/python

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Module docstring.

usage:
    Run this program with a single argument
    specifying a folder containing the following:
        p1.txt,p2.txt, ... pn.txt: for each page that
        you would like a glossary generated.

            If you would like line numbers that differ
            from the ones defined by the "newlines"
            in the given px.txt files then use the
            following annotation syntax:
                .# @text for line
            where # is the desired line number.
            Use \@ to include an @ symbol as a regular
            part of the file. The newline will
            indicate the end of the line.
            Use \\\@ To get \@ in the file.
        
        ignore.txt: an optional file containing a list of
        words that are to be ignored each on a new line
             ie.
             the\n
             he\n
             she\n
             cat\n
             
    The output will be as follows.
        gAll.txt: complete alphabetically sorted glossary
        of words in the page files. Each line has the
        word , page: n1 , line: n2

        g1.txt, g2.txt, gn.txt: the generated glossary
        for each page sorted by first occurance.


    Future improvments?
        Include frequency information and sorted.
        Use other information aside from newlines to
        deteremine the associated line number for a
        particular collection of words.
        eg .# @ line1 @ .# @ line2 @
        without using \n.
        Exclude phrases not just words.
        Use a stemming algorithm
   TODO remove capitalization requirement, chain ignores across files
"""

import getopt, os, sys, re,codecs
import unicodedata
fileEncoding = 'UTF-16' #also might want to try 'UTF-8' or 'ISO-8859-1'

"""From http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string"""
def strip_accents(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

def readFile(fName):
    f = openFile(fName)
    lines = f.readlines()
    f.close()
    return lines

def openFile(fName, mode = u"rb"):
    f = codecs.open(fName,mode,fileEncoding)
    return f
    

#"pnumber.txt"
pageFilePat    = r"p\d+.*\.txt$"
pageFilePatGrp    = re.compile(r"p(?u)(\d+).*\.txt$")
#"Matches '.number anything @ text'" as long as @ isn't preceded by \
lineCommandPat = re.compile( r"\A\.(\d+).*(?<!\\)@" ) 

class UsageError(Exception):
    def __init__(self,msg):
        self.msg = msg

class ParseError(Exception):
    def __init__(self,msg):
        self.msg = msg

"""Comparison function used to write out glossary based on order of occurence in f1 (file 1) and f2."""
def occurCmp(w1,w2):
    inf1 = w1[1]
    inf2 = w2[1]

    if inf1 < inf2:
        return -1
    elif inf1 > inf2:
        return 1
    return spanishCmp(w1,w2)


"""Ignores accents which leads to regular spanish sorting"""
def spanishCmp(w1,w2):
    word1 = strip_accents(w1[0])
    word2 = strip_accents(w2[0])
    if  word1 < word2:
        return -1
    elif word1 > word2:
        return 1
    return 0


""""Represents a glossary object including file writing and reading functions."""
class Glossary(object):
    def readGlossaryFile(self, f ):
        lines = f.readlines()
        
        for line in lines:
            word, spc, rest = line.strip().partition(" ")
            numbers = re.findall("\d+",rest)
            pageN = "-1"
            lineN = "-1"
            freq  = 1
            if len(numbers) >= 1:
                pageN = numbers[0]
            if len(numbers) >= 2:
                lineN = numbers[1]
            if len(numbers) >= 3:
                freq = int(numbers[2])
            word = word.capitalize()
            self.updateWord( word, pageN, lineN, freq )


    def writeGlossary(self, f, alphaNum = True, cmp = None ): 
        items = list(self.wordsInf.iteritems())
        if cmp != None:
            items.sort(cmp)
        elif alphaNum:
            items.sort(spanishCmp)
        else:
            items.sort( occurCmp )

        lines = ["%-20s p. %5s l. %5s\n" % ( word.capitalize(), inf[0], inf[1] ) for word, inf in items ] 
        f.writelines(lines)

        

    def __init__(self ):
        self.wordsInf = {}

    def updateWord(self, word, pageN="-1", lineN = "-1", freq = 1):
        if type(word) == tuple and len(word) == 2 and len(word[1]) == 3:
            pageN = word[1][0]
            lineN = word[1][1]
            freq  = int(word[1][2])
            word  = word[0]

        existing = self.wordsInf.get( word, [ pageN, lineN, 0 ] )
        existing[2] += freq
        self.wordsInf[word] = existing

    def merge(self, other):
        for wordInf in other.wordsInf.iteritems():
            self.updateWord( wordInf )

    def contains(self, word):
        return wordsInf.has_key(word)

    def diff(self, other):
        res = Glossary()
        for word,inf in other.wordsInf.iteritems():
            if self.wordsInf.has_key(word):
                res.updateWord( (word, self.wordsInf.pop(word)) )
        return res


def main(argv=None):
    if argv == None:
        argv = sys.argv

    #Ensure that a folder is given as a command line argument
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
        except GetoptError, err:
            raise UsageError(err)

        if len(args) == 0:
            raise UsageError("Pages directory not specified.")

        pageDirPath = os.path.abspath(args[0])
        if not os.path.isdir(pageDirPath):
            raise UsageError("Pages path specified is not a directory.")
        
    except UsageError,err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "use --help for help."
        return 2


    #if the file is named p#.txt and is not a directory 
    pageFileNames   = [ os.path.join( pageDirPath, fName ) 
                       for fName in os.listdir(pageDirPath) 
                       if re.match(pageFilePat, fName, re.I) != None ]
    pageFileNames   = [ fName for fName in pageFileNames 
                       if os.path.isfile(fName) ]

    #Reorder according to numbers
    pageFileNumbers = [ int(pageFilePatGrp.search(name).group(1)) 
                        for name in pageFileNames ]
    numberedPages = zip(pageFileNumbers,pageFileNames)
    numberedPages.sort();
    _,pageFileNames = zip(*numberedPages)
    #print pageFileNames

    #process ignore list
    ignoreGloss = Glossary()
    ignorePath = os.path.join( pageDirPath,"gignore.txt" )
    if os.path.isfile( ignorePath ):
        f = openFile( ignorePath,'r' )
        ignoreGloss.readGlossaryFile(f)
        f.close()

    pageGlossSets = []
    totalGloss = Glossary()
    for pageN,pageFileName in numberedPages:
        f = openFile(pageFileName,'r')
        lines = f.readlines()
        f.close()
        gloss = getPageGloss(lines, pageN)
        resI = gloss.diff(ignoreGloss)
        ignoreGloss.merge(resI)
        resT = gloss.diff(totalGloss)
        totalGloss.merge(gloss)
        totalGloss.merge(resT)

        pageGlossSets.append( (pageN, gloss) )
    
    for pageN, gloss in pageGlossSets:
        fout = openFile( os.path.join( pageDirPath,"gp%s.txt" % pageN) ,'w')
        gloss.writeGlossary(fout, False)
        fout.close()
    fout = openFile( os.path.join(  pageDirPath,"gall" + str(os.path.basename(pageDirPath)).lower() + ".txt"),'w' )
    totalGloss.writeGlossary(fout,True)
    fout.close()

    
#Generates and fills out a new Glossary
def getPageGloss(lines,pageN = "-1"):
    gloss  = Glossary() 
    
    lineN = 1
    for line in lines:
        annot = lineCommandPat.match(line)
        
        #If there is no line numbering annotation
        if annot == None:
            lineN = lineN + 1
        else:
            #exists by definition of lineCommandPat
            lineN = int(annot.group(1))

        line = cleanUpLine(line)
        for word in line.split():
            gloss.updateWord(word, pageN, lineN, 1)
    return gloss

def cleanUpWord(word):
    import string
    import unicodedata
    word = [ x for x in word if not (unicodedata.category(x)[0] in ('P','C','Z','N')) ]

    return u''.join(word).capitalize()
    #return word.strip(string.whitespace + string.punctuation + string.digits).capitalize()

def cleanUpLine(line):
    oLine = " ".join( [ cleanUpWord(word) for word in line.split() ] )
    #print oLine
    return oLine

if __name__ == "__main__":
    sys.exit(main())
