import pyaudio

class Audio:
    def __init__(self, channels, rlength):
        self.output = "output.wav"
        
        self.format = pyaudio.paInt16
        self.record_length = rlength
        self.chunk = 1024
        self.sr = 44100
        self.bps = 16
        self.channels = channels
        
        self.pa = pyaudio.PyAudio()
        
    def gen_header(self):
        sampleRate=self.sr
        bitsPerSample=self.bps
        channels=self.channels
        datasize = 2000*10**6
        h = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
        h += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
        h += bytes("WAVE",'ascii')                                              # (4byte) File type
        h += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
        h += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
        h += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
        h += (channels).to_bytes(2,'little')                                    # (2byte)
        h += (sampleRate).to_bytes(4,'little')                                  # (4byte)
        h += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
        h += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
        h += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
        h += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
        h += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
        return h

    def stream(self):
        print("starting audio stream")
        chunk = self.chunk
        sampleRate = self.sr
        bitsPerSample = self.bps
        channels = self.channels
        
        #print("setting header")
        #wav_header = self.genHeader(sampleRate, bitsPerSample, channels)
        
        print("setting up stream")
        stream = self.pa.open(format=self.format,
                              channels=channels,
                              rate=sampleRate,
                              input=True,
                              input_device_index=2,
                              frames_per_buffer=chunk)
        return stream
        