import os
import sys
import math
from bitarray import bitarray
from heapq import heappush, heappop
searchBufferSize = 4000
lookaheadBufferSize = 15

class heapNode(object):
    def __init__(self):
        self.left = None
        self.right = None
        self.counts = 0
        self.twelveBitInteger = ""
    def __lt__(self, other):
        return self.counts < other.counts

def printAndGetHuffmanTable(root,curPath,codes,verbose): # takes a huffman tree and generates huffman table and can also print it

    if root.left is None and root.right is None and root.twelveBitInteger:
        if verbose:
            print(curPath,"->",'{0:012b}'.format(root.twelveBitInteger))
        codes['{0:012b}'.format(root.twelveBitInteger)] = curPath
        return
    else:
        printAndGetHuffmanTable(root.left,curPath+"0",codes,verbose)
        printAndGetHuffmanTable(root.right,curPath+"1",codes,verbose)

def getBinaryFromTree(root,buffer): # do preorder traversal to copy tree to file in binary
    if root.left is None and root.right is None: # if leaf node
        buffer.append(False)
        bestDistanceLengthBinary = '{0:012b}'.format(root.twelveBitInteger)
        for bit in bestDistanceLengthBinary:
            if bit == '1':
                buffer.append(True)
            else:
                buffer.append(False)
    else:
        buffer.append(True) # internal nodes will be 1
        getBinaryFromTree(root.left,buffer)
        getBinaryFromTree(root.right,buffer)

def getTreeFromBinary(buffer): # do preorder traversal to construct new copy of binary tree
    nextBit = buffer.pop(0)
    if nextBit == False: # if leaf node
        root = heapNode()
        binaryString = ""
        for i in range(12):# read next twelve bytes to get full code
            bit = buffer.pop(0)
            if bit == True:
                binaryString+="1"
            else:
                binaryString+="0"

        root.twelveBitInteger = int(binaryString, 2)
    else:
        root = heapNode()
        root.left = getTreeFromBinary(buffer)
        root.right = getTreeFromBinary(buffer)

    return root


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
        dataForTree = None
        i = 0
        j = 0
        distances = []
        outputBuffer = bitarray(endian='big') 
        with open(inputFile, 'rb') as input_file:
            fileData = input_file.read()
            dataForTree = fileData

        while j < len(dataForTree): # get all the distance numbers so we can use the huffman coding algorithm on them
            pointer2 = getLongestSubstring(dataForTree, j)
            if pointer2: 
                (bestDistance, bestLength) = pointer2
                distances.append(bestDistance)
                j += bestLength
            else:
                j+=1

        counts = {}
        heap = []
        for distance in distances: # get counts of all numbers
            if distance in counts:
                counts[distance]+=1
            else:
                counts[distance] = 1

        for key in counts: # push nodes with 12bitintegers onto min heap
            node = heapNode()
            node.twelveBitInteger = key
            node.counts = counts[key]
            heappush(heap,node)
        # next create huffman tree by popping two smallest numbers and creating a new internal node with its counts being the sum of the counts of the two nodes that were popped
        root = None
        while len(heap)>1: 
            smallestNode = heappop(heap)
            secondSmallestNode = heappop(heap)
            newRoot = heapNode()
            newRoot.counts = smallestNode.counts + secondSmallestNode.counts
            newRoot.twelveBitInteger = ''
            newRoot.left = smallestNode
            newRoot.right = secondSmallestNode
            root = newRoot
            heappush(heap,newRoot)
        codeDictionary = {}
        printAndGetHuffmanTable(root,'',codeDictionary,False) # get the huffman table from tree
        treeBuffer = bitarray(endian='big')
        getBinaryFromTree(root,treeBuffer) # convert tree into string of bits

        
        while i < len(fileData): # constantly moves where the search and lookahead buffers would start [searchBuffer(max size = searchBufferSize)|i|lookaheadBuffer]
            pointer = getLongestSubstring(fileData, i)
       
            if pointer: 
                # Format follows 1 bit flag, 12 bits for the distance and 4 bits for the length of the substring
                # Means the maximum distance is 4095 and the maximum length is 15
                (bestDistance, bestLength) = pointer
                outputBuffer.append(True) # append flag along with distance and length to outputBuffer in binary format
                huffmanCode = codeDictionary['{0:012b}'.format(bestDistance)] # get the huffman code corresponding to the 12 bit integer
                bestDistanceLengthBinary = huffmanCode + '{0:04b}'.format(bestLength)
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
        # make sure newBuffer is multiple of 8
        newBuffer = treeBuffer + outputBuffer # treebuffer will be parsed first then the rest of the data
        newBuffer.fill()
        
        # write binary fileData to new file
        inputFile = inputFile.replace('.','') # remove file extension from file name
        with open(inputFile+".bin", 'wb') as outFile:
                outFile.write(newBuffer.tobytes())
                print("File compressed succesfully")
                return None

def decompress(inputFile, outputFile):
        fileData = bitarray(endian='big')
        outputBuffer = []
        with open(inputFile, 'rb') as input_file:
            fileData.fromfile(input_file)
        codeDictionary = {}
        root = getTreeFromBinary(fileData)
        printAndGetHuffmanTable(root,"",codeDictionary,False)
        while len(fileData) >= 9: # keep decompressing fileData while there are more then 8 bits left
            curbitsubstring = ""
            flag = fileData.pop(0) # get the first bit of the current char/char sequence to be decoded
            if not flag: # if just a single char then get next 8 bits and append to outputBuffer
                byte = fileData[0:8].tobytes()
                outputBuffer.append(byte)
                del fileData[0:8]
            else: # next bits will be the huffman code 
                
                bestLengthBinary = ""
                
                stop = False
                while stop == False: # compare each bit subsequence and see if it is in the huffman table
                    bit = fileData.pop(0)
                    if bit == True:
                        curbitsubstring+="1"
                    else:
                        curbitsubstring+="0"
                    for key in codeDictionary:
                        if codeDictionary[key] == str(curbitsubstring):
                            twelvebitnumber = key # if found in table then set the twelve bit number
                            stop = True
        
                for i in range(0,4): # get next 4 bits
                    bit=fileData.pop(0)
                    if bit == True:
                        bestLengthBinary+='1'
                    else:
                        bestLengthBinary+='0'
                bestDistance = int(twelvebitnumber, 2) # convert binary string to int
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

inputFile = 'myDEFLATE.py'
compress(inputFile)
decompress('myDEFLATEpy.bin','newDEFLATE.py')
