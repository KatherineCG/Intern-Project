"""
email library
"""
import os
basicpath = os.getcwd()
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import mimetypes, os, smtplib
from commonUtil import SCRIPT_USER, SCRIPT_PATH
from logger import getLogger

logger = getLogger()

SPLIT_LINE = '\n' + '-' * 50 + '\n'
AUTHOR = 'jingjiec'
DEFAULT_FROM_USER = 'bugzilla_reporter@vmware.com'
INVALID_RECIPIENTS = ['root']

def _indentMsg(msg):
   return "<pre>%s</pre>" % msg

def _addDomain(ldap):
   if '@' not in ldap:
      ldap = '%s@vmware.com' % ldap
   return ldap

def _addDomains(aliasList):
   if not aliasList:
      return

   for i in range(len(aliasList)):
      aliasList[i] = _addDomain(aliasList[i])

def sendEmail(subject, htmlMsg, images = None, files=None,
              toUser=None, sender=None, ccUser=None):
   # Create message container - the correct MIME type is multipart/alternative.
   emailHandler = MIMEMultipart('mixed')
   emailHandler['Subject'] = subject
   recipients = [AUTHOR, SCRIPT_USER]
   if toUser:
      recipients.extend(toUser)
   '''
   if ccUser:
      ccUser.append(SCRIPT_USER)
   else:
      ccUser = [SCRIPT_USER]
   '''
   toUser = list(set(toUser))
   ccUser = list(set(ccUser))
   recipients = list(set(recipients))
   recipients.extend(ccUser)
   for invalidRecipient in INVALID_RECIPIENTS:
      if invalidRecipient in recipients:
         logger.warn("Cannot send email to user %s, please use option -e to "
                     "specify ldap user name" % invalidRecipient)
         recipients.remove('root')

   _addDomains(recipients)
   if not sender:
      sender = DEFAULT_FROM_USER
   else:
      sender = _addDomain(sender)
   _addDomains(toUser)
   _addDomains(ccUser)
   emailHandler['From'] = sender
   emailHandler['To'] = ', '.join(toUser)
   emailHandler['Cc'] = ', '.join(ccUser)
   emailHandler['Bcc']= _addDomain(AUTHOR)
   emailText = '''\
      <html>
        <head></head>
        <body>
      '''
   emailText += _indentMsg(htmlMsg)
   emailText += '''\
     </body>
   </html>
   '''
   partemailHandler = MIMEText(emailText, 'html')
   emailHandler.attach(partemailHandler)

   if images:
      imagesParts = _generateEmailImage(images)
      if imagesParts:
         for imagePart in imagesParts:
            emailHandler.attach(imagePart)

   if files:
      attachParts = _generateEmailAttachment(files)
      if attachParts:
         for attachPart in attachParts:
            emailHandler.attach(attachPart)

   s = smtplib.SMTP('smtp.vmware.com')
   s.sendmail(sender, recipients, emailHandler.as_string())
   s.quit()

   logger.info('Email with title %s \nhas sent out through email, to-list: %r and cc: %r',
               subject, toUser, ccUser)
   logger.warn("If you want more LDAP users to receive this email, please define option -e before run this script")
   if images:
      logger.debug('Images have already sent out through email')
   if files:
      logger.debug('Files have already sent out through email')
      for fileName in files:
         logger.debug('Deleting attached file %s from local...', fileName)
         os.remove(fileName)

def _generateEmailImage(images):
   imagesParts = []
   for image in images:
      '''
      if not os.path.isfile(image):
         image = os.path
         logger.warn("Image %s not exist" % image)
         continue
      '''
      fp = open(basicpath+image, 'rb')
      msgImage = MIMEImage(fp.read())
      fp.close()
      msgImage.add_header('Content-ID', '<image' + image + '>')
      imagesParts.append(msgImage)
   return imagesParts

def _generateEmailAttachment(files):
   attachParts = []
   for afile in files:
      if not os.path.isfile(afile):
         afile = os.path
         logger.warn("File %s not exist, skip attach it to email" % afile)
         continue

      ctype, encoding = mimetypes.guess_type(afile)

      if ctype is None or encoding is not None:
         ctype = 'application/octet-stream'

      maintype, subtype = ctype.split('/', 1)
      with open(afile, 'r') as fp:
         content = fp.read()
         fp.close()
      if maintype == 'text':
         part = MIMEText(content)
      else:
         part = MIMEBase(maintype, subtype)
         part.set_payload(content)
         part.add_header('Content-Transfer-Encoding', 'base64')
         encoders.encode_base64(part)

      fileName = os.path.basename(afile)
      part.add_header('Content-Disposition', 'attachment; filename="%s"' % fileName)
      attachParts.append(part)

   return attachParts


if __name__ == '__main__':
   toUser = ['kaiyuanli', 'root', 'root', 'kaiyuanli']

   from htmlUtil import boldMsg, colorMsg, italicMsg, fontsizeMsg
   msg = [boldMsg('vmcore-main', 5),
          boldMsg(italicMsg('vmcore-main', 4)),
          fontsizeMsg('vmcore-main', 3),
          colorMsg('vmcore-main', 'darkblue')]
   htmlMsg = _indentMsg('\n'.join(msg))
   print htmlMsg

   sendEmail('Email Test', htmlMsg, toUser=toUser)
