'''
Library to handle html output
Created on Dec 24, 2015

@author: kaiyuanli
'''
# HTML default args
TITLE_L1_SIZE = 5
TITLE_L1_COLOR = 'darkblue'
TITLE_L2_SIZE = 4
HIGHLIGH_SIZE = 3

HTML_TAG_BR = '<br>'

def genHyperLink(content, hyperlink):
   return '<a href=%s>%s</a>' % (hyperlink, content)

def convertLineBreakFromPlain2Html(strInfo):
   return strInfo.replace('\n', HTML_TAG_BR)

def addLineBreak(line=2):
   return HTML_TAG_BR * line

def fontsizeMsg(msg, keySize):
   """Modify the font size @keySize of message @msg
   """
   if not keySize:
      keySize = 3
   return '<font size=%s>%s</font>' % (keySize, msg)

def boldMsg(msg, keySize=None, wrap=False):
   """bold message @msg with @keySize font size
   """
   if keySize:
      msg = fontsizeMsg(msg, keySize=keySize)
   boldedMsg = '<b>%s</b>' % msg
   if wrap:
      return '%s\n' % boldedMsg
   else:
      return boldedMsg

def italicMsg(msg, keySize=None, wrap=False):
   """italic message @msg with @keySize font size
   """
   if keySize:
      msg = fontsizeMsg(msg, keySize)
   italicedMsg = '<i>%s</i>' % msg
   if wrap:
      return '%s\n' % italicedMsg
   else:
      return italicedMsg

def colorMsg(msg, color='red'):
   return '<font color="%s">%s</font>' % (color, msg)

def tableMsg(inputMsg, backgroudInfo=[], redlineInfo=[], orangelineInfo = [], rednote=None, orangenote=None, splitFlag=None):
   totalInfo = '<TABLE border=1 cellspacing=0 bordercolorlight=#333333>\n'
   isred = False
   isorange = False
   remarkflag = False
   for i in range(len(inputMsg)):
      msg = '<TR>\n'
      if inputMsg[i][0] in redlineInfo:
          isred = True
      if inputMsg[i][0] in orangelineInfo:
          isorange = True
      for content in inputMsg[i]:
         if i == 0:
            BGCOLOR = ' BGCOLOR=#CCCCCC'
         elif content in backgroudInfo:
            BGCOLOR = ' BGCOLOR=#FFFF00'
         else:
            BGCOLOR = ''
         if isred:
             content = '<font color="FF0000">' + str(content) + '</font>'
         elif isorange:
             content = '<font color="D35400">' + str(content) + '</font>'
         else:
             content = str(content)
         if splitFlag:
            content = '<br>'.join(content.split(splitFlag))
         msg += '<TD%s>%s</TD>\n' % (BGCOLOR, content)
      if i == 0:
          if rednote or orangenote:
            msg += '<TD%s>%s</TD>\n' % (BGCOLOR, str('Remarks'))
            remarkflag = True
      else:
          if isred:
              rednote = '<font color="FF0000">' + str(rednote) + '</font>'
              msg += '<TD%s>%s</TD>\n' % (BGCOLOR, rednote)
          elif isorange:
              orangenote = '<font color="D35400">' + str(orangenote) + '</font>'
              msg += '<TD%s>%s</TD>\n' % (BGCOLOR, orangenote)
          elif remarkflag:
              msg += '<TD%s>%s</TD>\n' % (BGCOLOR, '')
      isred = False
      isorange = False
      msg += '</TR>\n'
      totalInfo += msg
   totalInfo += '</TABLE>'
   return totalInfo

def getHtmlTitle(msg, size=TITLE_L1_SIZE, color=TITLE_L1_COLOR):
   return colorMsg(boldMsg(msg, size), color=color)

def getEmailHeading(msg):
   return colorMsg(boldMsg(msg, TITLE_L1_SIZE), color=TITLE_L1_COLOR)

def getEmailHighLight(msg):
   """Generate bold and italic message
   """
   return boldMsg(msg, HIGHLIGH_SIZE)

def generateHtmlReport(bodyContent):
   return "<html>\n<body>\n%s\n</body>\n</html>" % bodyContent

if __name__ == '__main__':
    info = [['#', 'Workload Name', 'vmcore-main', 'vmcore-main-stage', 'vim-main-stage', 'networking-main-stage', 'storage-main-stage', 'vmkernel-main-stage', 'bfg-main-stage', 'main-stage'],
            [12, 'testesxgroup-uw_long', '15554', '9779, 302', '8594', '8594', '10949', '10949', '302', '2367'],
            [15, 'testesxgroup-vmkctl', '15263', '7196, 9779, 7196', '8594', '1803', '10946', '10946', '7196,302', '2367'],
            [16, 'testesxgroup-vmkdump', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', '2367'],
            [17, 'testesxgroup-vmkgdb', '15554', '9779, 302', '8594', '8594', '10949', '10949', '302', '2367'],
            [18, 'testesxgroup-vmklinux_bc55', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', '2367'],
            [19, 'testesxgroup-vmklinuxapi', '691', '302, 7172', '8594', '8594', '10949', '10949', '302', '2367']]


    msg = tableMsg(info, ['N/A'])
    print(msg)

    print(addLineBreak(5))

    test = 'hello world'
    print(getEmailHeading(test))
    print(getEmailHighLight(test))
    print(colorMsg(test))
    print(boldMsg(test))
    print(addLineBreak(3))
    print(italicMsg(test))

