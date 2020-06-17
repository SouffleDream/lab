#!/usr/bin/env python

from argparse import ArgumentParser
import threading
import os
from time import time
import args as args

barrier = threading.Barrier(3)
lock = threading.Lock()

def argument():

    # Make the argument prog list
    parser = ArgumentParser(description='Steganography')

    parser.add_argument("-s", "--size", type=int, default=1024, help="Reading block")
    parser.add_argument("-f", "--file", default="dog.ppm", help="PPM file, Image to analized")
    parser.add_argument("-m", "--message", default="message.txt", help="Steganographic message")
    parser.add_argument("-of", "--offset", type=int, default=15, help="Offset in pixels of raster start")
    parser.add_argument("-i", "--interleave", type=int, default=10, help="pixel mod interleave")
    parser.add_argument("-o", "--output", default="output_message.ppm", help="Stego-message")

    return parser.parse_args()

def verify_error(args):
    # Verify there is no problem
    if args.offset <= 0 or args.interleave <= 0 or args.size <= 0:
        print("\n***ERROR***")
        print("Values have to be higher than zero")
        exit(-1)


    try:
        file = os.open(args.file, os.O_RDONLY)  # open the ppm image
        message = os.open(args.message, os.O_RDONLY)    #open the steganographic message
    except FileNotFoundError:
        print("\n***ERROR***")
        print("Opening file failed")
        exit(-1)

    return [file, message]


def offset(read):
    lines = read.count(b"\n#")
    for i in range(lines):
        begin_comment = read.find(b"\n#") + 1
        end_comment = read.find(b"\n", begin_comment)

    if lines == 0:
        end_comment = read.find(b"\n")
    # P6/n comment/n dimension/n deep/n HEADER
    dimension = read.find(b"\n", end_comment + 1)
    deep = read.find(b"\n", dimension + 1)

    return deep + 1

def read_Message(message, size):
    mes = os.open(message, os.O_RDONLY)
    mes_read = os.read(mes, size)
    mesage = []
    for i in mes_read:
        mesage.append("{0:b}".format(i))
    count = 0
    for caract in mesage:
        for j in range(8-(len(caract))):
            charact = "0" + caract
        mesage[count] = charact
        count += 1
    mes_bin = ""
    for k in mesage:
        mes_bin += k
    l_total = len(mes_bin)
    return mes_bin, l_total


def steganography(message, pixels, begin_message, indice_pixel, interleave):

    indice = begin_message
    end = 0

    for i in range(indice_pixel, len(pixels), interleave*9):
        if indice > (len(message)-1):
            break

        # transform en binary the pixel
        bin="{0:b}".format(pixels[i]) #string
        bin = bin[0:-1]+(message[indice])
        pixels[i] = int(bin, 2)
    barrier.wait()
    return pixels


def outputMessage(red, blue, green, output, header):
    pixels = []

    for i in range(0, len(red)-2, 3):
        pixels.add(red[i])
        pixels.add(green[i+1])
        pixels.add(blue[i+2])

    try:
        output = os.open(args.output, "wb")  # open the ppm image
    except FileNotFoundError:
        print("\n***ERROR***")
        print("Opening file failed")
        exit(-1)
    pixels.append(header, output)
    barrier.wait()



if __name__ == '__main__':
    args = argument()  # Begin with the definition of the argument list
    start_time = time()
    [file, message] = verify_error(args)  # Verify if the file have no error before beginning
    #message = message.encode('ascii')
    message, l_total = read_Message(args.message, args.size) #Read the message to encrypt

    ##Definition of header
    size_header = 100  # definition of size max for header

    read = os.read(file, size_header)  # read the file
    offset = offset(read)  # calcul offset
    header = read[:offset]  # read the information of ppm file (number of cols and lines, and the encoding)
    comment = "#UMCOMPU2 {} {} {}\n".format(args.offset, args.interleave, l_total)
    header = (read[0:2], "\n", comment, read[2:])
    os.lseek(file, offset, 0)  # Position the read / write head in the file

    output = open(args.output, "wb", os.O_CREAT)

    # Definition of the first valor for each color
    begin_red = 0
    begin_green = 1 + args.interleave * 3
    begin_blue = 2 + 2 * args.interleave * 3

    # Definition of the indice of valor of each pixel
    indice_red = 0
    indice_green = 1
    indice_blue = 2

    # Define the width of the message (end when the entire message is encrypted)
    while True:
        lock.acquire()
        #mes = message.read(l_total)
        pixels = [i for i in message]
        lock.release()
        barrier.wait()

    # Creation of 3 thread, one for each color
    thread_red = threading.Thread(target=steganography, args=(message, pixels, begin_red, indice_red, args.interleave))
    thread_blue = threading.Thread(target=steganography, args=(message, pixels, begin_blue, indice_blue, args.interleave))
    thread_green = threading.Thread(target=steganography, args=(message, pixels, begin_green, indice_green, args.interleave))

    # Begin the process
    thread_red.start()
    thread_blue.start()
    thread_green.start()

    # Wait for all threads to complete
    red = thread_red.join()
    blue = thread_blue.join()
    green = thread_green.join()

    outputMessage(red, blue, green, args.output, header)

    if indice_red >= len(message) and indice_green >= len(message) and indice_blue >= len(message):
        print("The output_message have been generated.\n Duration: ", (time()-start_time))
        exit(-1)

    message.close()
    args.file.close()
    args.output.close()