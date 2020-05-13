#!/usr/bin/env python

from multiprocessing import Process, Queue
from argparse import ArgumentParser
import os
import args as args


def argument():

    # Make the argument prog list
    parser = ArgumentParser(description='Split ppm image into red, green and blue')

    parser.add_argument("-r", "--red", type=int, default=1, help="Red Filter")
    parser.add_argument("-g", "--green", type=int, default=1, help="Green Filter")
    parser.add_argument("-b", "--blue", type=int, default=1, help="Blue Filter")
    parser.add_argument("-f", "--file", type=str, default="image.ppm",help="PPM file, Image to be modified")
    parser.add_argument("-s", "--size", type=int, default=2048, help="Reading block")

    return parser.parse_args()


def verify_error(args):
    # Verify there is no problem
    if args.blue <= 0 or args.red <= 0 or args.green <= 0:
        print("\n***ERROR***")
        print("Values have to be higher than zero")
        exit(-1)

    if args.size <= 0:
        print("\n***ERROR***")
        print("The size of the read block must be an integer higher than zero")
        exit(-1)

    try:
        archive = os.open(args.file, os.O_RDONLY)  # open the ppm image
    except:
        print("\n***ERROR***")
        print("Opening file failed")
        exit(-1)

    return archive


def offset(read):
    lines = read.count(b"\n#")
    for i in range(lines):
        begin_comment = read.find(b"\n#") + 1
        end_comment = read.find(b"\n", begin_comment)

    if lines == 0:
        end_comment = read.find(b"\n")
    # P6/n dimension/n deep/n HEADER
    dimension = read.find(b"\n", end_comment + 1)
    deep = read.find(b"\n", dimension + 1)

    return deep + 1


def try_process(queue, idColor, doc):
    if idColor == 0:
        name = "red_filter.ppm"  # define the name file for red filter
    elif idColor == 1:
        name = "green_filter.ppm"  # define the name file for green filter
    elif idColor == 2:
        name = "blue_filter.ppm"  # define the name file for blue filter

    fd = os.open(name, os.O_WRONLY | os.O_CREAT)  # generation of fd for each RGB filter

    while True:
        if not queue.empty():  # verify if we are not at the end of the queue. That means, we did the 3 sons
            read = queue.get() #recup the information queue
            if (read == "EOF"):  # stop loop at the end of the queue
                break
            if type(read) == list:  # if the message is a list, I scroll through it and write down on the file. The message can be the header (bytes)
                msj = ""
                for i in range(len(read)):
                    if (type(read[i]) == int):  # if the values are int, we change it for string
                        msj += str(int(read[i] * doc))  # we add the values
                    else:
                        msj += str(read[i])
                read = msj.encode() #encode the queue with the right valor
            os.write(fd, read) #Write into the ppm filter file
    os.close(fd)
    exit(0)


def multiprocess(header):
    queues = []  # Creation of 3 queues for the 3 sons
    for i in range(3):
        queues.append(Queue())
        queues[i].put(header) #Add the header part for each sons

    process = []  # Creation of 3 sons, one for each color
    for i in range(3):
        if i == 0:
            doc = args.red
        elif i == 1:
            doc = args.green
        elif i == 2:
            doc = args.blue

        process.append(Process(target=try_process, args=(queues[i], i, doc)))
        process[i].start()  # Start multiprocessing
    return [process, queues]


def change_color(file, queues):
    y = 0
    while True:
        lu = os.read(file, args.size)
        for i in lu:
            if y%3 == 0:
                queues[y%3].put([i, " 0 0 "])  # Put every pixel with encoding for filter red
            elif y%3 == 1:
                queues[y%3].put(["0 ", i, " 0 "])  # Put every pixel with encoding for filter green
            elif y%3 == 2:
                queues[y%3].put(["0 0 ", i, " "])  # Put every pixel with encoding for filter blue
            y += 1
            if y%(20*3) == 0:
                queues[0].put(["\n"])
                queues[1].put(["\n"])
                queues[2].put(["\n"])
        break

    for y in range(3):
        queues[y].put("EOF")
    os.close(file)



if __name__ == '__main__':
    args = argument()  # Begin with the definition of the argument list
    file = verify_error(args)  # Verify if the file have no error before beginning

    ##Definition of header
    size_header = 100  # definition of size max for header

    read = os.read(file, size_header)  # read the file

    offset = offset(read)  # calcul offset
    header = read[:offset]  # read the information of ppm file (number of cols and lines, and the encoding)
    header = header.replace(b'P6',
                            b'P3')  # replace magic number P6 (ppm in binary) to P3 (ppm in ASCII coded with RGB color)

    os.lseek(file, offset, 0)  # Position the read / write head in the file

    ##Start multiprocessing part and changing color
    tab = multiprocess(header)  #return the process and the 3 sons in a tab
    process = tab[0]
    queues = tab[1]
    change_color(file, queues)  #change the color following the color filter for each sons
    for i in range(3):
        process[i].join()

    path = os.getcwd()  # get the curent folder
    for element in os.listdir(path):
        if element.endswith('.ppm'):
            print(element) #print all ppm files present in the current directory
