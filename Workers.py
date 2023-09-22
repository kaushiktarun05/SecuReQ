from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from block import Block, getModules
import time
import os
import importlib
import sys


class Fetch_Worker(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        ...


class Upload_Worker(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        ...


class RFID_Worker(QThread):
    '''RFID Working Thread Class'''
    ##### Signal for GUI Slots #####
    logsAppendSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    finishedSignal = pyqtSignal(int, QThread)

    def __init__(self, rfid, tagData=None, op='Read'):
        super().__init__()

        self.rfid = rfid
        self.tagData = tagData
        self.op = op
        # set the signals for GUI communication
        self.rfid.setSignals(self.logsAppendSignal)

    @pyqtSlot()
    def run(self):
        '''The Main Process for the Thread'''
        if self.op == 'Read':
            stat = self.rfid.readKey()
            key = str(self.rfid.getKey())
            # print(f"THE KEY #{key}")
            # print(type(key))
            self.resultSignal.emit(key)
            self.finishedSignal.emit(stat, self)
        else:
            stat = self.rfid.writeKey(self.tagData)
            self.finishedSignal.emit(stat, self)


class KeyGen_Worker(QThread):
    '''Key Generator Worker Thread Class'''
    logsAppendSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    finishedSignal = pyqtSignal()

    def __init__(self, algo, bit_size):
        super().__init__()
        self.algo = algo
        self.bit_size = bit_size
        print("CONSTR")

    def run(self) -> str:
        # TODO some kind of progress indicator for long
        i = 0
        while (i != 2):
            self.logsAppendSignal.emit(str(i))
            time.sleep(0.1)
            i += 1
        try:
            module = getModules()[self.algo]
            result = eval(f"module.{self.algo}.generateKey({self.bit_size})")
            print(f'Result: {result}')
            if eval(f"module.{self.algo}.isAsymmetric()"):
                ass_key = str(f'{result[0]}_{result[1]}')
                self.resultSignal.emit(ass_key)
                # return ass_key
                self.finishedSignal.emit()
            else:
                self.resultSignal.emit(str(result))
                self.finishedSignal.emit()
        except Exception as e:
            print(f'Worker Result {e}')
            return result
        #     self.resultSignal.emit(None)
        #     self.finishedSignal.emit()


class Cryptor_Worker(QThread):
    '''Working Crytor Thread Class'''
    logsAppendSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    finishedSignal = pyqtSignal()

    def __init__(self, size, algo, mode, isEnc, text, key, fpga = None):
        '''
        Cryptor Worker Constructor
        Args:
            size (int): bit size of blocks
            algo (str): encryption or decryption algorithm
            mode (str): mode of block
            isEnc (bool): is Encryption, else Decryption
            text (str): text to encrypt or decrypt
            key (str): algorithm key
            "optional" 
            fpga (FPGA): attach FPGA to algorithm
        '''
        super().__init__()
        self.isEnc = isEnc
        self.text = text
        print(f'Key {key}')
        # print(f'Key type {type(key)}')
        print(f'Text {text}')
        # print(f'Text type {type(text)}')
        module = getModules()[algo]
        self.isAss = eval(f"module.{algo}.isAsymmetric()")
        if fpga != None:
            if self.isAss:
                key = key.split('_')
                if self.isEnc:
                    self.block = Block(blockSize=size, 
                                    algo=algo, mode=mode, 
                                    isEnc=isEnc, text=text, 
                                    key=key[0], fpga=fpga)
                else:
                    self.block = Block(blockSize=size, 
                                    algo=algo, mode=mode, 
                                    isEnc=isEnc, text=text, 
                                    key=key[1], fpga=fpga)
            else:
                self.block = Block(blockSize=size, 
                                    algo=algo, mode=mode, 
                                    isEnc=isEnc, text=text, 
                                    key=key, fpga=fpga)
        else: # SORRU SORRY
            if self.isAss:
                key = key.split('_')
                if self.isEnc:
                    self.block = Block(blockSize=size, 
                                    algo=algo, mode=mode, 
                                    isEnc=isEnc, text=text, 
                                    key=key[0])
                else:
                    self.block = Block(blockSize=size, 
                                    algo=algo, mode=mode, 
                                    isEnc=isEnc, text=text, 
                                    key=key[1])
            else:
                self.block = Block(blockSize=size, 
                                    algo=algo, mode=mode, 
                                    isEnc=isEnc, text=text, 
                                    key=key)

    def run(self):
        '''The Main Process for the Thread'''
        try:
            result = self.block.run()
            print(f'Worker Result {result}')
            self.resultSignal.emit(result)
            # return result
            self.finishedSignal.emit()
        except Exception as e:
            print(f'Worker Result {e}')
        #     self.resultSignal.emit(None)
        #     self.finishedSignal.emit()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    # cryptor = KeyGen_Worker("DES", 64)
    # cryptor.start()
    # sys.exit(app.exec_())
    algo = 'RSA'
    # mode = 'ECB'
    mode = 'CBC'
    size = 16
    # key_gen = KeyGen_Worker(algo=algo, bit_size=size)
    # key = key_gen.start()
    # time.sleep(1)
    # key = '744b$ad59_fb$ad59'
    # key = '1783$9d37_8b$9d37'
    res = getModules()[algo].RSA.generateKey(size)  # ascii string
    key = str(f'{res[0]}_{res[1]}')
    # key = getModules()[algo].RSA.generateKey(size)  # ascii string
    # key = ('10001$f0c792cb', 'e4f319c1$f0c792cb')
    # key = '43123$48443_187$48443'
    # key = ('4117$20567', '133$20567')
    print(f"\nKEY all {key}")
    # message = "RSA ECB"
    # message = "E460"
    # message = "HI RSA CBC EE46"
    message = "RSA CBC"
    # fpga = RSA_FPGA()
    # message = "Hi"
    print("\n-------------(RSA - Enc - ECB)----------------")
    block = Cryptor_Worker(size=size, algo=algo, mode=mode,
                    isEnc=True, text=message, key=key)
    #                 # isEnc=True, text=message, key=key, fpga=fpga)
    time.sleep(0.2)
    cipher = block.run()
    time.sleep(0.2)
    print("plainHex is: " + message.encode().hex())
    print("key is: " + key.split('_')[0])
    print("cipher is: " + cipher)
    print("\n-------------(Decryption)----------------")
    block2 = Cryptor_Worker(size=size, algo=algo, mode=mode,
                    isEnc=False, text=cipher, key=key)
    #                 # isEnc=False, text=cipher, key=key, fpga=fpga)
    time.sleep(0.2)
    orig = block2.run()
    time.sleep(0.2)
    print("key is: " + key.split('_')[1])
    print("originalis: " + orig)
    bytesOrig = bytes.fromhex(orig)
    plain = bytesOrig.decode("utf-8")
    print(plain)
    # cryptor
    # rsa = __modules__['RSA'].RSA()
    # rsa.makeKeyFiles('RSA_demo', 32)
    ...
