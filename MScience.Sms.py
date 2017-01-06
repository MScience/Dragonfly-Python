import urllib.request
import xml.etree.ElementTree as ET
import pprint
import datetime

SmsNamespaces = {'msc': 'http://www.m-science.com/MScienceSMSWebService/','soapenv':'http://schemas.xmlsoap.org/soap/envelope/'}

for prefix in SmsNamespaces.keys():
    ET.register_namespace(prefix,SmsNamespaces[prefix])

"""This is a class that does something"""
class SmsClient:

    def __init__(self, accountId, password, primaryUri, backupUri):
        self._accountId = SmsClient._encryptString(accountId)
        self._password = SmsClient._encryptString(password)
        self._primaryUri = "http://smswebservice1.m-science.com/MScienceSMSWebService.asmx"
        self._backupUri = "http://smswebservice2.m-science.com/MScienceSMSWebService.asmx"

               
    def send(self, messages):
        sendMessagesElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}SendMessages")
        sourceTagElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}sourceTag")
        sourceAddressElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}sourceAddress")
        deliveryReceiptElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}deliveryReceipt")
        productMessageIdElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}productMessageID")
        destinationElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}destination")
        messageElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}message")

        sendMessagesElement.append(sourceTagElement)
        sendMessagesElement.append(sourceAddressElement)
        sendMessagesElement.append(deliveryReceiptElement)
        sendMessagesElement.append(productMessageIdElement)
        sendMessagesElement.append(destinationElement)
        sendMessagesElement.append(messageElement)


        for message in messages:
            sourceTagElement.append(SmsClient._createStringElement('Python API'))
            sourceAddressElement.append(SmsClient._createStringElement(message.Source()))
            if(message.DeliveryReport()):
                deliveryReceiptElement.append(SmsClient._createIntElement("1"))
            else:
                deliveryReceiptElement.append(SmsClient._createIntElement("0"))
            productMessageIdElement.append(SmsClient._createIntElement(str(message.SourceId())))
            destinationElement.append(SmsClient._createStringElement(message.Destination()))
            messageElement.append(SmsClient._createStringElement(message.Text()))
            

        result = self._send(self._primaryUri, sendMessagesElement,''.join([SmsNamespaces['msc'], 'SendMessages']))
        print(result)
        root = ET.fromstring(result)
        resultText = root.findtext('.//msc:SendMessagesResult', namespaces=SmsNamespaces)
        return SendResult.fromResultString(resultText)

    def _send(self, url, messageContent, soapAction):
        self._setSOAPAuthentication(messageContent)
        soapEnvelope = SmsClient._createSOAPEnvelope(messageContent)
        messageText = ET.tostring(soapEnvelope,encoding='UTF-8',method='xml')
        print(messageText)
        req = urllib.request.Request(url, messageText, {'Content-Type':'text/xml; charset=utf-8', 'soapAction':soapAction})
        
        result = urllib.request.urlopen(req).read().decode()
        return result

    @staticmethod
    def _createStringElement(value):
        element = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}string")
        element.text = value
        return element

    @staticmethod
    def _createIntElement(value):
        element = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}int")
        element.text = value
        return element

    @staticmethod
    def _createSOAPEnvelope(content):
        envelope = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope")
        body = ET.Element("{http://schemas.xmlsoap.org/soap/envelope/}Body")
        body.append(content)
        envelope.append(body)
        return envelope

    @staticmethod
    def _encryptString(input):
        output = str()
        for item in input:
            output = ''.join([output,chr(ord(item) + 1)])
        return output
        
    def getMessageStatus(self, messages):
        """Returns an array of StatusResult for the supplied message Ids"""
        getStatusElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}GetMessageStatus")

        messagesElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}messageID")

        for message in messages:
            messageId = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}int")
            messageId.text = str(message)
            messagesElement.append(messageId)

        getStatusElement.append(messagesElement)

        result = self._send(self._primaryUri, getStatusElement, "http://www.m-science.com/MScienceSMSWebService/GetMessageStatus")

        root = ET.fromstring(result)
        resultText = root.findtext('.//msc:GetMessageStatusResult',namespaces=SmsNamespaces)

        return Result.fromResultString(resultText)
       
    def _setSOAPAuthentication(self, message):
        encryptElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}encrypt")
        encryptElement.text = '1'
        message.append(encryptElement)

        accountIdElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}accountID")
        accountIdElement.text = self._accountId
        message.append(accountIdElement)

        passwordElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}password")
        passwordElement.text = self._password
        message.append(passwordElement)

    def getInboundStatus(self, address):
        """Returns an array of inbound messages and automatically acknowledges their receipt"""
        action = ''.join([SmsNamespaces['msc'] , 'GetURLStatus'])
        
        getStatusElement = ET.Element('{http://www.m-science.com/MScienceSMSWebService/}GetURLStatus')
        addressElement = ET.Element('{http://www.m-science.com/MScienceSMSWebService/}address')
        addressElement.text = address
        getStatusElement.append(addressElement)


        result = self._send(self._primaryUri, getStatusElement, action)
        root = ET.fromstring(result)
        resultString = root.findtext('.//msc:GetURLStatusResult', namespaces=SmsNamespaces)

        return Result.fromResultString(resultString)[0]

    def registerInbound(self, addresses):
        registerInboundElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}RegisterForInbound")
        addressElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}address")

        for address in addresses:
            stringElement = ET.Element('{http://www.m-science.com/MScienceSMSWebService/}string')
            stringElement.text = address
            addressElement.append(stringElement)

        registerInboundElement.append(addressElement)

        result = self._send(self._primaryUri, registerInboundElement, ''.join([SmsNamespaces['msc'],'RegisterForInbound']))
        root = ET.fromstring(result)
        resultText = root.findtext('.//msc:RegisterForInboundResult', namespaces=SmsNamespaces)

        return Result.fromResultString(resultText)

    def removeInbound(self, addresses):
        unregisterInboundElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}UnregisterInboundAddress")
        addressElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}address")
        unregisterInboundElement.append(addressElement)

        for address in addresses:
            stringElement = ET.Element('{http://www.m-science.com/MScienceSMSWebService/}string')
            stringElement.text = address
            addressElement.append(stringElement)


        result = self._send(self._primaryUri, unregisterInboundElement, ''.join([SmsNamespaces['msc'],'UnregisterInboundAddress']))
        root = ET.fromstring(result)
        resultText = root.findtext('.//msc:UnregisterInboundAddressResult', namespaces=SmsNamespaces)

        return Result.fromResultString(resultText)

    def clearInbound(self):
        """Clears all registered inbound addresses associated with the supplied AccountId"""
        clearInboundElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}ResetInboundCallbacks")
        action = ''.join([SmsNamespaces['msc'],'ResetInboundCallbacks'])
        
        result = self._send(self._primaryUri, clearInboundElement, action)
        root = ET.fromstring(result)
        resultText = root.findtext('.//msc:ResetInboundCallbacksResult', namespaces=SmsNamespaces)

        return Result.fromResultString(resultText)

    def getInboundMessages(self):
        """Returns an array of inbound messages and automatically acknowledges their receipt"""
        results = []

        messages = self._getInboundMessages()

        for message in messages:
            if not message.DeliveryReceipt():
                results.append(message)

        if(len(results) > 0):
            self._ackMessages(self._primaryUri, results)

        return results

    def getDeliveryReceipts(self):
        """Returns an array of delivery receipts and automatically acknowledges receiving them"""
        results = []

        messages = self._getInboundMessages()

        for message in messages:
            if message.DeliveryReceipt():
                results.append(message)

        if(len(results) > 0):
            self._ackMessages(self._primaryUri, results)

        return results

    def _getInboundMessages(self):
        getInboundElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}GetNextInboundMessages")

        result = self._send(self._primaryUri, getInboundElement, "http://www.m-science.com/MScienceSMSWebService/GetNextInboundMessages")
        root = ET.fromstring(result)

        resultText = root.findtext('.//msc:GetNextInboundMessagesResult', namespaces=SmsNamespaces)

        if(resultText is None):
            return []
        else:
            return InboundMessageResult.fromResultString(resultText)

    def _ackMessages(self, uri, messages):
        ackMessagesElement = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}AckMessages")

        arrayOfInt = ET.Element("{http://www.m-science.com/MScienceSMSWebService/}messageID")
        ackMessagesElement.append(arrayOfInt)

        for message in messages:
            intElement = ET.Element('{http://www.m-science.com/MScienceSMSWebService/}int')
            intElement.text = message.Id()
            arrayOfInt.append(intElement)

        result = self._send(uri, ackMessagesElement, 'http://www.m-science.com/MScienceSMSWebService/AckMessages')
        root = ET.fromstring(result)

        return root.text


class SendResult:
    def MessageId(self):
        return self._messageId

    def MessageBalance(self):
        return self._messageBalance

    def PendingMessages(self):
        return self._pendingMessages

    def SurchargeBalance(self):
        return self._surchargeBalance

    def ErrorMessage(self):
        return self._errorMessage

    def HasError(self):
        return len(self._errorMessage) > 0

    def __init__(self, code, messageId=0, messageBalance=0, pendingMessages=0, surchargeBalance=0, errorMessage=''):
        self._code = code
        self._messageId = messageId
        self._messageBalance = messageBalance
        self._pendingMessages = pendingMessages
        self._surchargeBalance = surchargeBalance
        self._errorMessage = errorMessage

    @staticmethod
    def fromResultString(input):
        results = []

        if (input == None or str.isspace(input)):
            return results

        inputParts = input.split(',,')

        for singleResult in inputParts:
            resultParts = singleResult.split(',')
            
            if "OK" in resultParts[0].upper():
            
                successParts = resultParts[0].split(',')
                statusIdPart = successParts[0].split('-')
                    
                if not statusIdPart[1].isdigit():
                    raise ValueError("Parsing failed. Unable to get message id")

                if not resultParts[1].isdecimal():
                    raise ValueError("Parsing failed. Unable to get message balance")
                    
                if not resultParts[2].isdigit():
                    raise ValueError("Parsing failed. Unable to get pending message count")

                if isinstance(resultParts[3], float):
                    raise ValueError("Parsing failed. Unable to get surcharge balance")
                
                results.append(SendResult(resultParts[0], statusIdPart[1], resultParts[1], resultParts[2], resultParts[3]))
            else:
                errorCode = resultParts[0].split('-')
                results.append(SendResult(resultParts[0], errorMessage = errorCode[1]))
     

        return results

class SmsMessage:
    def __init__(self, source, destination, sourceId, text, deliveryReport):
        self._source = source
        self._destination = destination
        self._sourceId = sourceId
        self._text = text
        self._deliveryReport = deliveryReport

    def Source(self):
        return self._source

    def Text(self):
        return self._text

    def Destination(self):
        return self._destination

    def DeliveryReport(self):
        return self._deliveryReport

    def SourceId(self):
        return self._sourceId

class InboundMessageResult:
        def Code(self):
            return self._code

        def Id(self):
            return self._id

        def Source(self):
            return self._source

        def Destination(self):
            return self._destination

        def Received(self):
            return self._received

        def SourceId(self):
            return self._sourceId

        def DeliveryReceipt(self):
            return self._deliveryReceipt

        def Text(self):
            return self._text

        def HasError(self):
            return len(self._errorMessage) > 0

        def ErrorMessage(self):
            return self._errorMessage

        def __init__(self, code, id=0, source='', destination='', received=datetime.datetime.fromordinal(1), sourceId='', deliveryReceipt=False, text='', errorMessage=''):
            self._code = code
            self._id = id
            self._source = source
            self._destination = destination
            self._received = received
            self._sourceId = sourceId
            self._deliveryReceipt = deliveryReceipt
            self._text = text
            self._errorMessage = errorMessage

        @staticmethod
        def fromResultString(input):
            """Returns an array of InboundMessageResult instances for the given input string"""
            results = []
            if input is None:
                return results

            index = input.find('-')
            code = input[: index]
            if code == "OK":
                input = input[3:]
                if input != "NOMESSAGES":
                    while len(input) > 0  and input != ',,':
                        if str.startswith(input,",,"):
                            input = input[2:]

                        message = InboundMessageResult.parseForMessage(input)
                        successParts = message.split(',')

                        if not str.isdigit(successParts[0]):
                            raise ValueError("Parse inbound message failed. Could not parse Id")

                        productId = None
                        if successParts[4].isdigit():
                            productId = successParts[4]
                            
                        
                        deliveryReceipt = successParts[5] == "1"

                        received = datetime.datetime.strptime("20/12/2014 09:14:35", "%d/%m/%Y %H:%M:%S")

                        results.append(InboundMessageResult(code, successParts[0], successParts[1], successParts[2], received,
                                                             productId, deliveryReceipt, successParts[8]))

                        input = input[len(message):]
            else:
                results.append(InboundMessageResult(code, errorMessage = input.Substring(index + 1)))

            return results

        @staticmethod
        def parseForMessage(message):
            builder = str()

            parseCount = 0
            while parseCount < 8:
                endOfCurrentItem = message.find(",")

                if endOfCurrentItem == -1:
                    builder = builder + " " + message
                    #builder.Append(message)
                    break

                messagePart = message[: endOfCurrentItem]

                builder = ''.join([builder, messagePart, ','])
                message = message[endOfCurrentItem + 1:]

                if parseCount == 7:
                    byteCount = int(messagePart)
                    messageBytes = str.encode(message,encoding='ascii')
                    textBytes = messageBytes[:byteCount]
                    text = textBytes.decode('ascii')
                    builder = ''.join([builder,text])

                parseCount+=1

            return builder

class Result:
    def Code(self):
        return self._code
        
    def SubCode(self):
        return self._subCode

    def HasError(self):
        return self._code != "OK"

    def ErrorMessage(self):
       if self.HasError():
           return self._subCode
       else:
           return ''

    def __init__(self, code, subCode):
        self._code = code
        self._subCode = subCode


    @staticmethod
    def fromResultString(result):
        results = []

        if(result is None or result == ''):
            return results

        resultParts = result.split(',')

        for singleResult in resultParts:
            if(not singleResult is None and singleResult != ''):
                singleResultParts = singleResult.split('-')
                results.append(Result(singleResultParts[0],singleResultParts[1]))

        return results


#if __name__ == '__main__':
#    a = ['http://fred.co.uk/12345','http://fred.co.uk/12345']
#    f = SmsClient("46275","7Z0V5O0L1A","","")
#    g = f.send([SmsMessage("","+447921067264",0,"Test From Python",False),])

#    for res in g:
#        print(res.MessageId())
#        print(res.PendingMessages())
#        print(res.MessageBalance())
#        print(res.SurchargeBalance())
#        print(res.HasError())
#        print(res.ErrorMessage())

#        stat = f.getMessageStatus([res.MessageId(),])
#        for s in stat:
#            print(s.Code())
#            print(s.SubCode())




