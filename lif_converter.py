import sys,os,pickle

#reads pattern files in the "Life 1.05", "Life 1.06", and "Run-Length-Encoded" format
def converter(life_file):
    def get_info(line,info):
        if len(line) < 80:
            info.append(line[3:-1])
        else:
            splitat = line.rfind(" ",3,80)
            if splitat != -1:
                info.append(line[3:splitat])
                info.append(line[1+splitat:-1])
            else:  
                info.append(line[3:80])
                info.append(line[80:-1])
                            
    extension = life_file.lower()[-3:]
    #parses 'Life 1.05' and 'Life 1.06' pattern files
    if extension == "lif":
        block_start = (0,0)
        row         = 0
        info        = []
        lif = open(life_file,"r")
        structure = set()
        mytype = lif.readline()
        if   "#Life 1.05" in mytype:
            oneohfive = True
        elif "#Life 1.06" in mytype:
            oneohfive = False
        if oneohfive:
            #Life 1.05
            for line in lif:
                if "#P" in line[:2]:
                    nums = line[3:].split(" ")
                    block_start  = (int(nums[0]),int(nums[1]))
                    row = 0
                elif "#D" in line[:2]:
                    get_info(line,info)
                elif line[0] != '#' and ("."  in line or "*" in line):
                    for col,char in enumerate(line):
                        if char == "*":
                            structure |= set(((block_start[0]+col,block_start[1]+row),))
                    row += 1
        else:
            #Life 1.06
            for line in lif:
                if "#P" in line[:2]:
                    nums = line[3:].split(" ")
                    block_start  = (int(nums[0]),int(nums[1]))
                    row = 0
                elif "#D" in line[:2]:
                    get_info(line,info)
                elif line[0] != "#":
                    point = line.split(" ")
                    structure |= set(((int(point[0]),int(point[1])),))
            
    #parses 'Run-Length-Encoded' pattern files
    elif extension == "rle":
        block_start = (0,0)
        row         = 0
        col         = 0
        colchar     = ""
        colint      = 0
        done        = False
        info        = []
        lif = open(life_file,"r")
        structure = set()
        for line in lif:
            if line[:2] in ("#P","#R"):
                nums = line[3:].split(" ")
                block_start  = (int(nums[0]),int(nums[1]))
                row = 0
            elif line[:2] in ("#D","#N","#C"):
                get_info(line,info)
            elif line[0] == "x":
                splitat = line.rfind("rule")
                if splitat != -1:
                    info.append("Bounding box: " + line[:splitat-2])
                    info.append("Rule: " + line[splitat+6:-1])
                else:
                    info.append("Bounding box: " + line[:-1])
            elif line[0] != '#' and ("$" in line or "!" in line):
                for char in line:
                    if "0" <= char <= "9":
                        colchar += char
                    elif char == "b":
                        if colchar:
                            col += int(colchar)
                        else:
                            col += 1
                        colchar = ""
                    elif char == "o":
                        if colchar:
                            for i in range(int(colchar)):
                                structure |= set(((block_start[0]+col,block_start[1]+row),))
                                col += 1
                        else:
                            structure |= set(((block_start[0]+col,block_start[1]+row),))
                            col += 1
                        colchar = ""
                    elif char == "$":
                        if colchar:
                            row += int(colchar)
                        else:
                            row += 1
                        colchar = ""
                        col     = 0
                    elif char == "!":
                        done = True
                if done:
                    break

    structure = recenter(structure)
    return(structure,info)

def get_preqs(pattern):
    A = set()
    B = set()
    for a,b in pattern:
        A |= set((a,))
        B |= set((b,))
    sizex = max(A)-min(A)
    sizey = max(B)-min(B)
    return (A,B,sizex,sizey)
    
def rot_clockwise(pattern):
    A,B,sizex,sizey = get_preqs(pattern)
    rotate = set()
    for a,b in pattern:
        rotate |= set(((sizey-b,a),))
    final = recenter(rotate)
    return final

def rot_counter(pattern):
    A,B,sizex,sizey = get_preqs(pattern)
    rotate = set()
    for a,b in pattern:
        rotate |= set(((b,sizex-a),))
    final = recenter(rotate)
    return final

def mirror_H(pattern):
    A,B,sizex,sizey = get_preqs(pattern)
    mirror = set()
    for a,b in pattern:
        mirror |= set(((a,sizey-b),))
    final = recenter(mirror)
    return final

def mirror_V(pattern):
    A,B,sizex,sizey = get_preqs(pattern)
    mirror = set()
    for a,b in pattern:
        mirror |= set(((sizex-a,b),))
    final = recenter(mirror)
    return final
    
def recenter(pattern):
    setX,setY,sizex,sizey = get_preqs(pattern)
    centered = set()
    for a,b in pattern:
        centered |= set(((a-min(setX)-sizex//2,b-min(setY)-sizey//2),))
    return centered

def image2cursor(image):
    w = image.get_width()
    h = image.get_height()

    if (w != h) or (w % 8 != 0):
        print("width and height must be equal and must be divisible by 8")
        return(-1)
    stringlist = []
    for col in range(h):
        colstring = ""
        for row in range(w):
            mypixel = image.get_at((row,col))
            if mypixel == (0,0,0):
                colstring += "X"
            elif mypixel == (255,255,255):
                colstring += "."
            else:
                colstring += " "
        stringlist.append(colstring)
    return stringlist

def convert2lif(pattern,directory):
    #saves the living cells on the screen in a Life 1.06 format (recenters first)
    myfile = open(os.path.join(directory,"savescreen.lif"),'w')
    myfile.write("#Life 1.06\n")
    mypattern = recenter(pattern)
    for cell in mypattern:
        myfile.write(str(cell[0])+" "+str(cell[1])+"\n")
    myfile.close
     
###
if __name__ == "__main__":
    secta = {(1,0),(2,0),(3,0),(0,1),(1,1),(1,2)}
    (mirror_H(secta))
    
    
