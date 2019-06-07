# Summer 2019. A tool for verifying that morecells and morelocs are consistent with eachother.
# Author: Avik Bosshardt




CELL_FILE_PATH = ''
LOC_FILE_PATH = ''


with open(CELL_FILE_PATH, 'r') as cellfile:
    with open(LOC_FILE_PATH, 'r') as locfile:
        loclines = locfile.readlines()
        celllines = cellfile.readlines()

        for i in range(len(loclines)):
            if loclines[i].split(' ')[-1] != celllines[i].split(' ')[-1]:
                print("Mismatch at line",i+1)
        else:
            print("No errors!")
