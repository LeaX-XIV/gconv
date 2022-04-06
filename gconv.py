#! python3

import sys
from enum import Flag, auto


class Setting(Flag):
    NIL = 0
    IN_V = auto()
    IN_E = auto()
    IN_BV = auto()
    OUT_V = auto()
    OUT_E = auto()
    OUT_BV = auto()
    NO_LOOP = auto()
    UNDIR = auto()
    SORT = auto()


def inputVertexList(lines):
    result = {}
    indexmap = {}
    nV, *lines = lines
    try:
        nV = int(nV)
    except ValueError as e:
        if '\t' in e:
            print(
                "ERROR: tried to open file with mode -v. Maybe you meant -e?")

    assert nV == len(lines),\
        f"Wrong number of lines in file. Expected {nV}, found {len(lines)}"

    for i in range(nV):
        line = lines[i]
        edges = line.split(":")
        v, edges = edges
        edges = edges.strip().split(' ')

        # edges = line.strip().split(' ')
        # v = i
        assert edges[-1] == '#', "Last element of line expected to be '#'"
        edges = edges[:-1]
        if str(v) in result.keys():
            raise ValueError("Declared twice vertex " + v)
        result[str(v)] = list(map(int, edges))
        indexmap[str(v)] = i

    # Correction for empty nodes not present
    correction = []
    for edges in result.values():
        for w in edges:
            if str(w) not in indexmap:
                correction.append(str(w))

    for w in correction:
        if w not in result.keys():
            result[w] = []
        if w not in indexmap:
            indexmap[w] = nV
            nV += 1

    return [result, indexmap]


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

        if str(w) not in result:
            result[str(w)] = []
        if str(w) not in indexmap:
            indexmap[str(w)] = i
            i += 1

    return [result, indexmap]


def inputBinaryVertex(chunk, result={}, indexmap={}):
    i = len(indexmap)
    v = None

    for j in range(0, len(chunk), 8):
        w = int.from_bytes(chunk[j:j + 8], byteorder="little", signed=True)

        if j == 0:
            assert w >= 0, f'Expected positive value, found {w}'

            v = str(w)
            if v not in indexmap:
                indexmap[v] = i
                i += 1

            result[v] = []
        else:
            if w < 0:
                break

            if str(w) not in indexmap:
                indexmap[str(w)] = i
                i += 1

            result[v].append(w)

    return [result, indexmap]


def removeLoops(nodeList, indexmap):
    for v, edges in nodeList.items():
        try:
            edges.remove(int(v))
        except ValueError:
            continue

    return [nodeList, indexmap]


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


def outputBinaryVertex(nodeList, indexmap, doSort, pad=-1):
    nEmax = len(max(nodeList.values(), key=len))
    indexmap['-1'] = -1
    output = list(len(nodeList).to_bytes(8, 'little', signed=True)) + \
            list(nEmax.to_bytes(8, 'little', signed=True))

    for v, edges in (sorted(nodeList.items(), \
                        key=lambda i: indexmap[i[0]]) if doSort \
                        else nodeList.items()):
        output += list(int(indexmap[v]).to_bytes(8, 'little', signed=True))
        edges = (sorted(edges, \
                    key=lambda e: indexmap[str(e)]) if doSort \
                    else edges)
        for w in (edges + [pad] * (nEmax - len(edges))):
            output += list(indexmap[str(w)].to_bytes(8, 'little', signed=True))
            yield bytearray(output)
            output = []


def convert(inF, outF, settings):
    nodes = {}
    indexmap = {}

    print(f"Loading {inF}...")

    assert len(Setting) == 10, "Exhaustive Setting definition"
    if settings & Setting.IN_E:
        with open(inF, 'r') as f:
            [nodes, indexmap] = inputEdgeList(f.readlines())
    elif settings & Setting.IN_V:
        with open(inF, 'r') as f:
            [nodes, indexmap] = inputVertexList(f.readlines())
    elif settings & Setting.IN_BV:
        with open(inF, 'rb') as f:
            nV = int.from_bytes(f.read(8), byteorder='little', signed=True)
            nEmax = int.from_bytes(f.read(8), byteorder='little', signed=True)
            for _ in range(nV):
                [nodes, indexmap] = inputBinaryVertex(f.read(8 * (1 + nEmax)),
                                                      nodes, indexmap)
    else:
        print(f"ERROR: inMode not specified")
        sys.exit(1)

    print("Loading complete!")

    assert len(Setting) == 10, "Exhaustive Setting definition"
    if settings & Setting.NO_LOOP:
        print("Removing looping edges...")
        [nodes, indexmap] = removeLoops(nodes, indexmap)
        print("Looping edges removed!")

    if settings & Setting.UNDIR:
        print("Checking graph for direct edges...")
        [nodes, indexmap] = checkUndir(nodes, indexmap)
        print("Graph is undirected!")

    print(f"Writing output file {outF}...")

    assert len(Setting) == 10, "Exhaustive Setting definition"
    if settings & Setting.OUT_E:
        with open(outF, 'w') as f:
            f.write(ouputEdgeList(nodes, indexmap, settings & Setting.SORT))
    elif settings & Setting.OUT_V:
        with open(outF, 'w') as f:
            f.write(ouputVertexList(nodes, indexmap, settings & Setting.SORT))
    elif settings & Setting.OUT_BV:
        with open(outF, 'wb') as f:
            for b in outputBinaryVertex(nodes, indexmap,
                                        settings & Setting.SORT):
                f.write(b)
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
    assert len(Setting) == 10, "Exhaustive Setting definition"
    print("Usage:")
    print(f"{sys.argv[0]} [CMD] | [MODE <graph_in> MODE <graph_out> OPT]")
    print("CMD:")
    print("\t-h\tPrint this message")
    print("MODE:")
    print("\t-v\tThe file is interpreted as a list of verteces")
    print("\t-e\tThe file is interpreted as a list of edges")
    print("\t-bv\tThe file is interpreted as binary list ov vertices")
    print("OPT:")
    print("\t-l\tDeletes self-looping edges")
    print("\t-u\tForce the output graph to be undirected")
    print("\t-s\tSort output ascending")


def main(args):
    settings = Setting.NIL
    inFile = None
    outFile = None

    assert len(Setting) == 10, "Exhaustive Setting definition"
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
                settings |= Setting.IN_V
                inFile = filename
            else:
                settings |= Setting.OUT_V
                outFile = filename
        elif arg == '-e':
            try:
                filename, args = extractArg(args)
            except KeyError:
                printUsage()
                sys.exit(0)

            if inFile == None:
                settings |= Setting.IN_E
                inFile = filename
            else:
                settings |= Setting.OUT_E
                outFile = filename
        elif arg == '-bv':
            try:
                filename, args = extractArg(args)
            except KeyError:
                printUsage()
                sys.exit(0)

            if inFile == None:
                settings |= Setting.IN_BV
                inFile = filename
            else:
                settings |= Setting.OUT_BV
                outFile = filename
        elif arg == '-l':
            settings |= Setting.NO_LOOP
        elif arg == '-u':
            settings |= Setting.UNDIR
        elif arg == '-s':
            settings |= Setting.SORT
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