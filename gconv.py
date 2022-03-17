#! python3

import sys
from enum import Flag, auto


class Settings(Flag):
    NIL = 0
    IN_V = auto()
    IN_E = auto()
    OUT_V = auto()
    OUT_E = auto()
    UNDIR = auto()
    SORT = auto()


def inputEdgeList(lines):
    result = {}
    indexmap = {}
    i = 0

    for line in lines:
        v, w, *_ = line.strip().split('\t')

        if str(v) not in result:
            result[str(v)] = [int(w)]

            if str(v) not in indexmap:
                indexmap[str(v)] = i
                i += 1
        else:
            result[str(v)].append(int(w))

        if str(w) not in indexmap:
            indexmap[str(w)] = i
            i += 1

    return [result, indexmap]


def inputVertexList(lines):
    result = {}
    indexmap = {}
    nV, *lines = lines
    nV = int(nV)

    assert nV == len(lines),\
        f"Wrong number of lines in file. Expected {nV}, found {len(lines)}"

    for i in range(nV):
        line = lines[i]
        edges = line.split(":")
        v, edges = edges

        edges = edges.strip().split(' ')
        assert edges[-1] == '#', "Last element of line expected to be '#'"
        edges = edges[:-1]
        result[str(v)] = list(map(int, edges))
        indexmap[str(v)] = i

    for edges in result.values():
        for w in edges:
            if str(w) not in indexmap:
                indexmap[str(w)] = nV
                nV += 1

    return [result, indexmap]


def checkUndir(nodeList, indexmap):
    missing = {}

    for v, edges in nodeList.items():
        for w in edges:
            try:
                if int(v) not in nodeList[str(w)]:
                    if len(missing) == 0:
                        print("INFO: Found direct edge in graph.")
                        print("Preparing correction data...")

                    if str(w) in missing:
                        missing[str(w)].append(int(v))
                    else:
                        missing[str(w)] = [int(v)]
            except KeyError:
                if str(w) not in missing:
                    if len(missing) == 0:
                        print("INFO: Found direct edge in graph.")
                        print("Preparing correction data...")

                    if str(w) in missing:
                        missing[str(w)].append(int(v))
                    else:
                        missing[str(w)] = [int(v)]

    if len(missing) > 0:
        print("Correction data is ready!")
        print("Correcting directness...")

        for key, value in missing.items():
            if key in nodeList:
                nodeList[str(key)].extend(value)
            else:
                nodeList[str(key)] = value

        print("Directness correction complete!")

    return [nodeList, indexmap]


def ouputVertexList(nodeList, indexmap, doSort):
    return f"{len(nodeList)}\n" + '\n'.join([
        f"{indexmap[v]}: " \
            + ' '.join([
                str(indexmap[str(e)]) for e in
                                    (sorted(edges, \
                                    key=lambda e: int(indexmap[str(e)])) if doSort \
                                    else edges)
                ])
            + " #"
        for v, edges in
            (sorted(nodeList.items(), \
                key=lambda i: indexmap[i[0]]) if doSort \
                else nodeList.items())
    ])


def ouputEdgeList(nodeList, indexmap, doSort):
    return '\n'.join([
        '\n'.join([
            f"{indexmap[str(v)]}\t{indexmap[str(w)]}"
            for w in
                (sorted(edges, \
                    key=lambda e: indexmap[str(e)]) if doSort \
                    else edges)
        ])
        for v, edges in
            (sorted(nodeList.items(), \
                key=lambda i: indexmap[i[0]]) if doSort \
                else nodeList.items())
    ])


def convert(inF, outF, settings):
    nodes = {}
    indexmap = {}

    with open(inF, 'r') as f:
        print(f"Loading {f.name}...")

        if settings & Settings.IN_E:
            [nodes, indexmap] = inputEdgeList(f.readlines())
        elif settings & Settings.IN_V:
            [nodes, indexmap] = inputVertexList(f.readlines())
        else:
            print(f"ERROR: inMode not specified")
            sys.exit(1)

    print("Loading complete!")

    if settings & Settings.UNDIR:
        print("Checking graph for direct edges...")
        [nodes, indexmap] = checkUndir(nodes, indexmap)
        print("Graph is undirected!")

    with open(outF, 'w') as f:
        print(f"Writing output file {f.name}...")
        if settings & Settings.OUT_E:
            f.write(ouputEdgeList(nodes, indexmap, settings & Settings.SORT))
        elif settings & Settings.OUT_V:
            f.write(ouputVertexList(nodes, indexmap, settings & Settings.SORT))
        else:
            print(f"ERROR: outMode not specified")
            sys.exit(1)

    print("Writing completed!")


def extractArg(args):
    if len(args) > 0:
        return args[0], args[1:]
    else:
        raise IndexError()


def printUsage():
    print("Usage:")
    print(f"{sys.argv[0]} [CMD] | [MODE <graph_in> MODE <graph_out> OPT]")
    print("CMD:")
    print("\t-h\tPrint this message")
    print("MODE:")
    print("\t-v\tThe file is interpreted as a list of verteces")
    print("\t-e\tThe file is interpreted as a list of edges")
    print("OPT:")
    print("\t-u\tForce the output graph to be undirected")
    print("\t-s\tSort output ascending")


def main(args):
    settings = Settings.NIL
    inFile = None
    outFile = None

    while len(args) > 0:
        arg, args = extractArg(args)

        if arg == '-h':
            printUsage()
            sys.exit(0)
        elif arg == '-v':
            try:
                filename, args = extractArg(args)
            except IndexError:
                printUsage()
                sys.exit(0)

            if inFile == None:
                settings |= Settings.IN_V
                inFile = filename
            else:
                settings |= Settings.OUT_V
                outFile = filename
        elif arg == '-e':
            try:
                filename, args = extractArg(args)
            except KeyError:
                printUsage()
                sys.exit(0)

            if inFile == None:
                settings |= Settings.IN_E
                inFile = filename
            else:
                settings |= Settings.OUT_E
                outFile = filename
        elif arg == '-u':
            settings |= Settings.UNDIR
        elif arg == '-s':
            settings |= Settings.SORT
        else:
            print(f"WARNING: Unrecognized parameter '{arg}' is being skipped.")

    if inFile != None and outFile != None:
        convert(inFile, outFile, settings)
    else:
        printUsage()
        sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
    print("DONE")