import os
import sys
import math
from bitarray import bitarray

searchBufferSize = 4000
lookaheadBufferSize = 15

def getLongestSubstring(fileData, i):
        # Finds the longest substring in the look ahead that matches a substring in the search Buffer
        startSearch = max(0, i - searchBufferSize)
        endOfLookahead = min(i + lookaheadBufferSize, len(fileData) + 1)
        bestDistance = 0
        bestLength = 0

        #######################################################################
        # [|startSearch|----------------|i|----------------|endOfLookahead|]  #
        # <--------searchBuffer---------><--------<lookaheadBuffer>---------> #
        #######################################################################
        
        mysearchbuffer = fileData[startSearch:i]
        lookaheadbuffer = fileData[i:endOfLookahead]
        lookaheadsubstringlength = 2 # only consider substrings of size 2
        while lookaheadsubstringlength < len(lookaheadbuffer): #keep generating substrings until we generate a substring of the enitre size of the lookahead buffer
            cursubstring = lookaheadbuffer[0:lookaheadsubstringlength]
            wassubstringfound = mysearchbuffer.rfind(cursubstring) # see if we can find the substring in the search buffer
            if wassubstringfound != -1:# if found then keep trying to match larger substrings, otherwise stop since largest substring was already found
                lookaheadsubstringlength+=1 
                if len(cursubstring) > bestLength:# keep track of largest substring
                    bestLength = len(cursubstring)
                    distancefromendofsearchbuffer = (i - startSearch) - wassubstringfound # this will be the "distance" from wherever the lookahead buffer begins
                    bestDistance = distancefromendofsearchbuffer
                    for j in range(len(cursubstring),len(lookaheadbuffer)):
                        if chr(lookaheadbuffer[j]) == chr(fileData[i-distancefromendofsearchbuffer+j]): # check if next char in lookahead buffer is the next char in the file fileData
                            bestLength+=1
                        else:
                            break
            else:
                break

        if bestDistance > 0 and bestLength > 0:  # return longest substring
            return (bestDistance, bestLength)
        else:
            return None

def compress(inputFile):
        fileData = None
        i = 0
        outputBuffer = bitarray(endian='big') 
        with open(inputFile, 'rb') as input_file:
            fileData = input_file.read()

        while i < len(fileData): # constantly moves where the search and lookahead buffers would start [searchBuffer(max size = searchBufferSize)|i|lookaheadBuffer]
            pointer = getLongestSubstring(fileData, i)
       
            if pointer: 
                # Format follows 1 bit flag, 12 bits for the distance and 4 bits for the length of the substring
                # Means the maximum distance is 4095 and the maximum length is 15
                (bestDistance, bestLength) = pointer
                outputBuffer.append(True) # append flag along with distance and length to outputBuffer in binary format
                bestDistanceLengthBinary = '{0:012b}'.format(bestDistance) + '{0:04b}'.format(bestLength)
                for bit in bestDistanceLengthBinary:
                    if bit == '1':
                        outputBuffer.append(True)
                    else:
                        outputBuffer.append(False)
                i += bestLength # increment i however many chars there are in the substring
            else:
                # If no match found in search Buffer then append flag and single char to outputBuffer in binary format
                # with the format following 1 bit as a flag and 8 bits for the char
                outputBuffer.append(False)
                outputBuffer.frombytes(bytes([fileData[i]]))
                i += 1
            
        # make sure outputBuffer is multiple of 8		
        outputBuffer.fill()

        # write binary fileData to new file
        inputFile = inputFile.replace('.','') # remove file extension from file name
        with open(inputFile+".bin", 'wb') as outFile:
                outFile.write(outputBuffer.tobytes())
                print("File compressed succesfully")
                return None

def decompress(inputFile, outputFile):
        fileData = bitarray(endian='big')
        outputBuffer = []
        with open(inputFile, 'rb') as input_file:
            fileData.fromfile(input_file)

        while len(fileData) >= 9: # keep decompressing fileData while there are more then 8 bits left

            flag = fileData.pop(0) # get the first bit of the current char/char sequence to be decoded
            if not flag: # if just a single char then get next 8 bits and append to outputBuffer
                byte = fileData[0:8].tobytes()
                outputBuffer.append(byte)
                del fileData[0:8]
            else: # else get the next 16 bits 
                bestDistanceBinary = ""
                bestLengthBinary = ""
                for i in range(0,12): # get first 12 bits
                    bit=fileData.pop(0)
                    if bit == True:
                        bestDistanceBinary+='1'
                    else:
                        bestDistanceBinary+='0'
                for i in range(0,4): # get next 4 bits
                    bit=fileData.pop(0)
                    if bit == True:
                        bestLengthBinary+='1'
                    else:
                        bestLengthBinary+='0'

                bestDistance = int(bestDistanceBinary, 2) # convert binary string to int
                bestLength = int(bestLengthBinary, 2) 
                for i in range(bestLength): # get the next "length" of chars from the current Buffer that start at "distance" away and append to outputBuffer
                    outputBuffer.append(outputBuffer[-bestDistance])
                    
        # convert output outputBuffer to binary data to write to file
        decompressedfileData =  b''.join(outputBuffer) 

        # write binary fileData to new file
        with open(outputFile, 'wb') as outFile:
            outFile.write(decompressedfileData)
            print('File was decompressed successfully')
            return None 

inputFile = 'myLZ77.py'
compress(inputFile)
decompress('myLZ77py.bin','newLZ77.py')
