
import platform
import ctypes
import random
from ctypes import *
import os
import time
from time import time, sleep

DEFAULT_SETTINGS =     [0x01,0x01,0x00,0x00,0x15,0x00,0x04]
SINGLE_READ_SETTINGS = [0x01,0x00,0x00,0x00,0x05,0x01,0x04]

class RFID:

##### Class Variables
    fOpenComIndex = None

##### Static Values
    ### FROM DATA SHEET
                # address # Baudrate # Scan Time 
    SETTINGS = [0xff,     0x06,      0x50]
    ZERO = 0

    # init method or constructor
    def __init__(self):

        ############################################################### Uncomment when you use the writer
        self.__setup_dll()
        self.openPort()
        print("opened COM ", self.fOpenComIndex.value)
        ############################################################### Uncomment when you use the writer
        # self.setDeviceSettings() # use when needed
        # self.getDeviceInfo() # use when needed
        # self.closePort() # use when needed
        print("constructed RFID")
        
########### DEVICE INITIALIZATION METHODS ############

    # Device setup
    def __setup_dll(self):
        if platform.system() == 'Windows':
            absolutepath = os.path.abspath(__file__)
            self.fileDirectory = os.path.dirname(absolutepath)
            self.Objdll = ctypes.windll.LoadLibrary(
                # Path 64 bit
                self.fileDirectory + '\\lib\\64 bit\\UHFReader09.dll')
                # fileDirectory + '\\lib\\64 bit\\ZK_RFID105.dll')
                # Path 32 bit
                # fileDirectory + '\\lib\\32 bit\\UHFReader09.dll')
        elif platform.system() == 'Linux':
            # absolutepath = os.path.abspath(__file__)
            # self.fileDirectory = os.path.dirname(absolutepath)
            # self.Objdll = ctypes.windll.LoadLibrary(
                # Path 64 bit
                # self.fileDirectory + '/lib/64 bit/UHFReader09.so')
            # TODO: MONO, IronPython, Pythonnet, Refrence issue, CLR, Basic.dll broken
            ...
        else:
            raise Exception(f"Device does not support {platform.system()} OS")


    def openPort(self, port = 0):
    # open serial communication port of writer
        fPort = c_int32(port)
        fComAdr = c_ubyte(self.SETTINGS[0])
        # fBaud = c_ubyte(0x06) # only when wish to change first time enter it manually
        fBaud = c_ubyte(self.SETTINGS[1])
        frmcomportindex = c_int32(0)
        if (port == 0): # when unknown port
            res = self.Objdll.AutoOpenComPort(byref(fPort),  byref(fComAdr),
                                        fBaud, byref(frmcomportindex)) #from here the handle
        else:           # when known port
            res = self.Objdll.OpenComPort(fPort,  byref(fComAdr),
                                        fBaud, byref(frmcomportindex)) #from here the handle
        if res == 0x00:   # open device
            print("Open Success")
            print(self.getReturnCodeDesc(res))
            self.fOpenComIndex = frmcomportindex
            self.fComAdr = fComAdr
        else:
            print("Open Failed")
            print(self.getReturnCodeDesc(res))

    def closePort(self, ComPortIndex = None):
    # close serial communication port of writer
        if (ComPortIndex == None):
            print("Force close port",self.fOpenComIndex.value)
            print(self.getReturnCodeDesc(self.Objdll.CloseComPort(self.fOpenComIndex)))
        else:
            print("Closing port", self.fOpenComIndex.value)
            print(self.getReturnCodeDesc(self.Objdll.CloseSpecComPort(ComPortIndex)))
    
    def setDeviceSettings(self):
    # set device settings as in SETTINGS LIST

        InventoryScanTime = c_ubyte(self.SETTINGS[2])
        res = self.Objdll.WriteScanTime(byref(self.fComAdr),
                        byref(InventoryScanTime), self.fOpenComIndex)
        if res == 0x00:   
            print("Set Scan time Success")
            print(self.getReturnCodeDesc(res))
        else:
            print("Set Scan time Failed")
            print(self.getReturnCodeDesc(res))

        # fBaud = c_ubyte(0x06)
        fBaud = c_ubyte(self.SETTINGS[1])
        res = self.Objdll.Writebaud(byref(self.fComAdr),
                        byref(fBaud), self.fOpenComIndex)
        if res == 0x00:   
            print("Set Baud rate Success")
            print(self.getReturnCodeDesc(res))
        else:
            print("Set Baud rate Failed")
            print(self.getReturnCodeDesc(res))

    def getDeviceInfo(self):
    # get the writers information
        VersionInfo = bytes(2)
        ReaderType = c_ubyte(0x00)
        TrType = bytes(2)
        dmaxfre = c_ubyte(0x00)
        dminfre = c_ubyte(0x00)
        powerdBm = c_ubyte(0x00)
        ScanTime = c_ubyte(0x00)
        
        res = self.Objdll.GetReaderInformation(byref(self.fComAdr),
                VersionInfo, byref(ReaderType),
                TrType, byref(dmaxfre), byref(dminfre),
                byref(powerdBm), byref(ScanTime), self.fOpenComIndex)
        if res == 0:
            print("get info Success")
        else:
            print("get info Failed")
            print(self.getReturnCodeDesc(res))
        
        print("fComAdr: ", hex(self.fComAdr.value))
        VersionText = VersionInfo.hex()
        print("Version: " + str(int(VersionText[:2],16)).rjust(2,'0')
                    +"."+ str(int(VersionText[2:],16)).rjust(2,'0'))
        if (ReaderType == 0x08):
            print("ReaderType: UHFReader09")
        if ((TrType[0] & 0x02) == 0x02):
            print("TrType: ISO180006B and EPCC1G2")
        print("powerdBm: ", powerdBm.value) # if 0 means unknown power
        print("ScanTime: " + str(ScanTime.value) + " ms")

        dmaxfre = int(dmaxfre.value)
        dminfre = int(dminfre.value)

        FreBand = ((dmaxfre & 0xc0) >> 4) | (dminfre >> 6)
        match (FreBand):
            case 0x00: # User Bandwidth
                    fdminfre = 902.6 + (dminfre & 0x3F) * 0.4
                    fdmaxfre = 902.6 + (dmaxfre & 0x3F) * 0.4
            case 0x01: # Chinese Bandwidth
                    fdminfre = 920.125 + (dminfre & 0x3F) * 0.25
                    fdmaxfre = 920.125 + (dmaxfre & 0x3F) * 0.25
            case 0x02: # US Bandwidth
                    fdminfre = 902.75 + (dminfre & 0x3F) * 0.5
                    fdmaxfre = 902.75 + (dmaxfre & 0x3F) * 0.5
            case 0x03: # Korean Bandwidth
                    fdminfre = 917.1 + (dminfre & 0x3F) * 0.2
                    fdmaxfre = 917.1 + (dmaxfre & 0x3F) * 0.2
            case 0x04: # EU Bandwidth
                    fdminfre = 865.1 + (dminfre & 0x3F) * 0.2
                    fdmaxfre = 865.1 + (dmaxfre & 0x3F) * 0.2
            case _:
                print("Invalid Frequency")
        print("dmaxfre: " + str(fdmaxfre) + "MHz")
        print("dminfre: " + str(fdminfre) + "MHz")

        # TODO no SN
        self.DeviceSN = str(random.randbytes(4).hex())
        print("DeviceSN: ", self.DeviceSN)

########## DEVICE OPERATION METHODS #########

    def detectNumberOfTags(self, num):
    # Checks wheather number of tags in front of read are of desired
    # return 0 when failed to reach amount of tags by iteration completion 
    # return 1 when successfully amount of tags
    # return 2 when surpassed amount of tags {to pop a window}
        uniqueTags = []
        i = 8 # iterations
        while(i!=0):
            i -= 1
            tagRead = self.readInvetory()
            if tagRead == None:
                continue
            if tagRead not in uniqueTags:
                # print("adding:")
                # print(tagRead)
                uniqueTags.append(tagRead)
            else:
                continue
            if (len(uniqueTags) > num):
                print(f'{num} tag only')
                # time.sleep(1)
                return 2
        if (len(uniqueTags) != num):
            return 0
        else:
            return 1

    def readInvetory(self):
        AdrTID  = c_ubyte(0x00)
        LenTID  = c_ubyte(0x00)
        TIDFlag = c_ubyte(0x00)
        CardNum = c_int32(0)
        Totallen = c_int32(0) #no use?

        while True:
            EPC = bytes(17)
            res = self.Objdll.Inventory_G2(byref(self.fComAdr), 
                AdrTID, LenTID, TIDFlag, EPC, 
                byref(Totallen), byref(CardNum), self.fOpenComIndex)
            if res == 0x01 or res == 0x00:
                print("Read Success")
                print(self.getReturnCodeDesc(res))
                print(EPC[1:])
                return EPC[1:]
            else:
                print("Read Failed")
                print(self.getReturnCodeDesc(res))
                return None

    def writeEPC(self, data, pswd = [0x00,0x00,0x00,0x00]):
    
        fPassWord   = bytes(pswd)
        WriteEPClen = c_ubyte(0x10) # 16 bytes length
        ferrorcode  = c_ubyte(0x00)

        res = self.Objdll.WriteEPC_G2(byref(self.fComAdr), 
            fPassWord, data, WriteEPClen,
            byref(ferrorcode), self.fOpenComIndex)
        if res == 0x00:
            print("Write Success")
            print("written: " + str(data))
        else:
            print("Write Failed")
            print(self.getReturnCodeDesc(res))

    # Check wheather desired data is on tag
    # input EPC pointer and it will check if written as desired
    def checkTag(self, desiredData = ZERO.to_bytes(16, 'big')
                ,pswd = [0x00,0x00,0x00,0x00]): 
        
        EPCpointer  = desiredData
        Mem         = c_ubyte(0x01) # EPC
        Num         = c_ubyte(0x08) # length in word
        WordPtr     = c_ubyte(0x02) #
        Maskadr     = c_ubyte(0x00)  # no point
        MaskLen     = c_ubyte(0x00)  # no point
        MaskFlag    = c_ubyte(0x00) # no point
        EPClength   = c_ubyte(0x00) # no point
        ferrorcode  = c_ubyte(0x00) #
        fPassWord   = bytes(pswd) #
        currentData = bytes(16) 

        # attempt a read of desired tag
        res = self.Objdll.ReadCard_G2(byref(self.fComAdr), 
            EPCpointer, Mem, WordPtr, Num, fPassWord,
            Maskadr,MaskLen,MaskFlag, 
            currentData, EPClength, byref(ferrorcode),
            self.fOpenComIndex)
        if res == 0:
            print("Read Success")
            print(self.getReturnCodeDesc(res))
            print("desiredData", desiredData)
            print("currentData", currentData)
            if (currentData == desiredData):
                return 1
            else:
                print("corrupt")
                return 0
        else:
            print("Read Failed")
            print(self.getReturnCodeDesc(res))
            return 0

##### HELPER METHODS

    def getReturnCodeDesc(self, cmdRet):
    # device methods results description
            match(cmdRet):
                case 0x00:
                    return "Operation Successful"
                case 0x01:
                    return "Return before Inventory finished"
                case 0x02:
                    return "the Inventory-scan-time overflow"
                case 0x03:
                    return "More Data"
                case 0x04:
                    return "Reader module MCU is Full"
                case 0x05:
                    return "Access Password Error"
                case 0x09:
                    return "Destroy Password Error"
                case 0x0a:
                    return "Destroy Password Error Cannot be Zero"
                case 0x0b:
                    return "Tag Not Support the command"
                case 0x0c:
                    return "Use the commmand, Access Password Cannot be Zero"
                case 0x0d:
                    return "Tag is protected, cannot set it again"
                case 0x0e:
                    return "Tag is unprotected, no need to reset it"
                case 0x10:
                    return "There is some locked bytes, write fail"
                case 0x11:
                    return "can not lock it"
                case 0x12:
                    return "is locked, cannot lock it again"
                case 0x13:
                    return "Parameter Save Fail,Can Use Before Power"
                case 0x14:
                    return "Cannot adjust"
                case 0x15:
                    return "Return before Inventory finished"
                case 0x16:
                    return "Inventory-Scan-Time overflow"
                case 0x17:
                    return "More Data"
                case 0x18:
                    return "Reader module MCU is full"
                case 0x19:
                    return "Not Support Command Or AccessPassword Cannot be Zero"
                case 0xFA:
                    return "Get Tag, Poor Communication, Inoperable"
                case 0xFB:
                    return "No Tag Operable"
                case 0xFC:
                    return "Tag Return ErrorCode"
                case 0xFD:
                    return "Command length wrong"
                case 0xFE:
                    return "Illegal command"
                case 0xFF:
                    return "Parameter Error"
                case 0x30:
                    return "Communication error"
                case 0x31:
                    return "CRC checksum error"
                case 0x32:
                    return "Return data length error"
                case 0x33:
                    return "Communication busy"
                case 0x34:
                    return "Busy, command is being executed"
                case 0x35:
                    return "ComPort Opened"
                case 0x36:
                    return "ComPort Closed"
                case 0x37:
                    return "Invalid Handle"
                case 0x38:
                    return "Invalid Port"
                case 0xEE:
                    return "Return command error"
                case _:
                    return "Some Other ERROR"

##### GUI Setup ######
    def setSignals(self, logsAppendSignal):
        self.logsAppendSignal = logsAppendSignal

##### GUI METHODS #####
    def writeKey(self, desiredDataToWrite):
        dataToWrite = bytes(desiredDataToWrite) # convert to bytes
        self.logsAppendSignal.emit("writing key...")
        writtenComplete = False
        numOfTags = 1
        attempt = 1
        attemptFilter = 10
        while not writtenComplete:
            # check if reader detects more than one tag
            stat = self.detectNumberOfTags(numOfTags)
            if stat == 2: # tags surpassed numOfTags
                return 2 # window pop
            if stat == 0: # tags != numOfTags
                self.logsAppendSignal.emit("incorrect amount of tags in front of reader")
                self.logsAppendSignal.emit(f"Place {numOfTags} tag infront of reader")
                attemptFilter -= 1
                if attemptFilter == 0:
                    return 0 # fail once attemptFilter 0 is reached
                continue
            else:
                self.logsAppendSignal.emit("attempt #" + str(attempt))
                # attempt to write on tag
                self.writeEPC(dataToWrite)
                # check wheather data has been written correctly or not
                if self.checkTag(dataToWrite) == 1:
                    writtenComplete = True
                else:
                    attempt += 1
                    if attempt == 6:
                        return 0 # fail once attempt 5 is reached
                    continue
        self.logsAppendSignal.emit("*******************")
        self.logsAppendSignal.emit("*******************")
        self.logsAppendSignal.emit("    Key Written    ")
        self.logsAppendSignal.emit("*******************")
        self.logsAppendSignal.emit("*******************")
        return 1

    def readKey(self):
    # When Read Tag Button is pressed in the GUI
    # return 0 when failed to read the tag
    # return 1 when successfully read tag
    # return 2 when surpassed amount of tags {to pop a window}
        # return 1
        self.logsAppendSignal.emit("Reading tag...")
        readComplete = False
        numOfTags = 1
        attempt = 1
        attemptFilter = 10

        while not readComplete:
            # check if reader detects more than one tag
            stat = self.detectNumberOfTags(numOfTags)
            if stat == 2: # tags surpassed numOfTags
                return 2 # window pop
            if stat == 0: # tags != numOfTags
                self.logsAppendSignal.emit("incorrect amount of tags in front of reader")
                self.logsAppendSignal.emit(f"Place {numOfTags} tag infront of reader")
                attemptFilter -= 1
                if attemptFilter == 0:
                    return 0 # fail once attemptFilter 0 is reached
                continue
            else:
                self.logsAppendSignal.emit("attempt #" + str(attempt))
                # attempt to read on tag
                tagRead = self.readInvetory()
                # check wheather data has been read correctly or not
                if tagRead != None:
                    readComplete = True
                else:
                    attempt += 1
                    if attempt == 6:
                        return 0 # fail once attempt 5 is reached
                    continue

        self.logsAppendSignal.emit("******************")
        self.logsAppendSignal.emit("******************")
        self.logsAppendSignal.emit("     Tag Read     ")
        self.logsAppendSignal.emit("******************")
        self.logsAppendSignal.emit("******************")
    
        # Decode tag info
        self.__key = tagRead.decode("utf-8")
        print(f"decode: {self.__key}")
        
        return 1

    def getKey(self):
        return self.__key

def main():
    rfid = RFID()
    # print("DDDDDDDDDDDDDDD")
    # rfid.closePort()
    ...

if __name__ == '__main__':
    main()