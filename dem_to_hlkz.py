import os, sys, struct

def get_vals(file, format):
    data = file.read(struct.calcsize(format))
    return struct.unpack(format, data)

class Demo:
    def __init__(self, demofile):
        self.demofile = demofile
        self.header = self.get_header()
        self.directories = self.get_directories()
        self.get_frames()

    def get_header(self):
        self.demofile.seek(0)
        vals = get_vals(self.demofile, '<8xII260s260sII')
        header = {}
        header["netProtocol"] = vals[0]
        header["demoProtocol"] = vals[1]
        header["mapName"] = vals[2]
        header["gameDir"] = vals[3]
        header["mapCRC"] = vals[4]
        header["directoryOffset"] = vals[5]
        return header

    def get_directories(self):
        self.demofile.seek(self.header["directoryOffset"])
        count = get_vals(self.demofile, '<I')[0]
        directories = []
        for _ in range(count):
            dir = {}
            data = self.demofile.read(struct.calcsize('<I64sI8xIII'))
            dir["offset"] = struct.unpack('<84xI4x', data)[0]
            # dir["frames"] = []
            directories.append(dir)
        return directories

    def get_frames(self):
        with open(sys.argv[1][:-4] + "_replay.dat", "wb") as replay:
            dir = self.directories[1] # for dir in self.directories?
            self.demofile.seek(dir["offset"])
            final_reached = False
            while not final_reached:
                frame = {}
                vals = get_vals(self.demofile, '<Bf4x')
                frame["type"] = vals[0]
                frame["time"] = vals[1]
                match vals[0]:
                    case 0 | 1: # NetMsg
                        frame_data = list(get_vals(self.demofile, '<4x6f238xH'))
                        frame_data[3] /= -3 # pitch is inverted & scaled
                        # view height is at 64 units, whereas we want to output
                        # origin at 36 units, so subtract the difference
                        frame_data[2] -= 28
                        replay.write(
                            struct.pack("7fH", frame["time"], *frame_data))
                        # frame["origin"] = frame_data[0:3]
                        # frame["viewangles"] = frame_data[3:6]
                        # frame["buttons"] = frame_data[6]
                        self.demofile.seek(196, os.SEEK_CUR)
                        msg_len = get_vals(self.demofile, '<i')[0]
                        self.demofile.seek(msg_len, os.SEEK_CUR)
                    case 2: # DEMO_START
                        pass
                    case 3: # CONSOLE_COMMAND
                        self.demofile.seek(64, os.SEEK_CUR)
                    case 4: # CLIENT_DATA
                        self.demofile.seek(32, os.SEEK_CUR)
                    case 5: # NEXT_SECTION
                        final_reached = True
                    case 6: # EVENT
                        self.demofile.seek(84, os.SEEK_CUR)
                    case 7: # WEAPON_ANIM
                        self.demofile.seek(8, os.SEEK_CUR)
                    case 8: # SOUND
                        sample_len = get_vals(self.demofile, '<4xI')[0]
                        self.demofile.seek(sample_len + 16, os.SEEK_CUR)
                    case 9: # DEMO_BUFFER
                        buffer_len = get_vals(self.demofile, '<i')[0]
                        self.demofile.seek(buffer_len, os.SEEK_CUR)
                    case _:
                        print("Error while parsing!")
                        exit(1)
                # dir["frames"].append(frame)
        print("done")

def main():
    if len(sys.argv) == 1:
        print("No demo given")
        return
    with open(sys.argv[1], "rb") as demofile:
        if demofile.read(8) != b'HLDEMO\x00\x00':
            print("Invalid format")
            return
        demo = Demo(demofile)

if __name__ == "__main__":
    main()
