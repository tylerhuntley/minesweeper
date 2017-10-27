import tkinter as tk
import random
import threading

DIFFICULTY = {'easy':{'width':9, 'height':9, 'mines':10},
              'medium':{'width':16, 'height':16, 'mines':40},
              'hard':{'width':30, 'height':16, 'mines':99}}

root = tk.Tk()

# Store global reference for each icon, to avoid recreating for each use
GIF = {'mine':tk.PhotoImage(file='mine.gif'),
       'flag':tk.PhotoImage(file='flag.gif'),
       'wrong':tk.PhotoImage(file='wrong.gif'),
       'smiley':tk.PhotoImage(file='smiley.gif'),
       'win':tk.PhotoImage(file='win.gif'),
       'lose':tk.PhotoImage(file='lose.gif'),
       't':{9:tk.PhotoImage(file='t{}.gif'.format(9)),
            '-':tk.PhotoImage(file='t-.gif')}}
for i in range(9):
    GIF[i] = tk.PhotoImage(file=str(i)+'.gif')
    GIF['t'][i] = tk.PhotoImage(file='t{}.gif'.format(i))


class App():
    def __init__(self, master):
        self.mode = DIFFICULTY['hard']
        self.height = self.mode['height']
        self.width = self.mode['width']
        self.mines = self.mode['mines']

        self.flags = 0
        self.swept = 0
        self.started = False
        self.ended = False

#        frame = tk.Frame(master)
#        frame.grid()

        self.field = tk.Frame(master, bd=3, padx=2, pady=2, relief='sunken')
        self.ui = tk.Frame(master, bd=3, padx=2, pady=2, relief='sunken')

        self.field.grid(row=1)
        self.ui.grid(row=0)
#        self.field.pack(fill='x', side='bottom')
#        self.ui.pack(fill='x')

        # Build button grid for minefield
        self.button = {}
        for x in range(self.width):
            for y in range(self.height):
                self.button[(x, y)] = Tile(self, x, y, self.field,
                            command=lambda x=x, y=y: self.click(x, y))
                self.button[(x, y)].grid(column=x, row=y)

        # Construct upper display UI
        self.score = Counter(master=self.ui, num=self.mines)
        self.reset_button = tk.Button(self.ui, image=GIF['smiley'], command=self.restart)
        self.time = Clock(master=self.ui, num=0)

        self.score.grid(column=0, row=0, sticky='E')
        self.reset_button.grid(column=1, row=0)
        self.time.grid(column=2, row=0, sticky='E')
#        self.score.pack(side='left')
#        self.reset_button.pack(fill='y')
#        self.time.pack(side='right')

    def click(self, x, y):
        if not self.started:
            self.start_game(x, y)
        if not self.ended:
            self.button[(x, y)].click()

    def get_tile(self, x, y):
        return self.button[(x, y)]

    def start_game(self, x, y):
        # Start the timer here, too...
        self.time.start()
        self.started = True
        self.place_mines(x, y)

    def place_mines(self, x, y):
        """Place mines randomly, but never on the first clicked square"""
        self.mine_list = []
        options = self.button.copy()
        del options[(x, y)]  # Remove initial square from options
        for xy in random.sample(list(options), self.mines):
            mine = Mine(self, *xy, self.field,
                       command=lambda xy=xy: self.button[xy].click())
            mine.grid(column=xy[0], row=xy[1])
            self.button[xy].grid_remove()
            self.button[xy] = mine
            self.mine_list.append(mine)

    def game_over(self, initial, win=False):
        self.ended = True
        self.time.stop()
        if win:
            self.reset_button['image'] = GIF['win']
        else:
            self.reset_button['image'] = GIF['lose']

        icon = [GIF['mine'], GIF['flag']]
        relief = ['sunken', 'raised']
        for mine in self.mine_list:
            if not mine is initial:
                mine.reveal(icon[win], relief[win])

    def restart(self):
        if not self.ended:
            self.game_over(None)
        self.field.grid_remove()
        self.ui.grid_remove()
        self.__init__(root)


class Tile(tk.Button):
    def __init__(self, app, x, y, *args, **kwargs):
        super().__init__(width=12, height=12, relief='raised', *args, **kwargs)
        self.image = GIF[0]
        self['image'] = self.image

        # Populate list of adjacent tiles, that exist
        self.adjacent = []
        for x2 in range(x-1, x+2):
            for y2 in range(y-1, y+2):
                if x2 in range(app.width) and y2 in range(app.height):
                    self.adjacent.append((x2, y2))
#        print(x,y, self.adjacent)
        self.adjacent.remove((x, y))

        self.mines_nearby = 0  # To be incremented by each mine
        self.clicked = False
        self.flagged = False
        self.bind('<Button-3>', self.flag)  # Bind right-click to flag()

    def click(self):
        if self.flagged or self.clicked:
            pass
        else:
            app.swept += 1
            self.clicked = True
            self['relief'] = 'sunken'
            self.image = GIF[self.mines_nearby]
            self['image'] = self.image
            if not self.mines_nearby:
                self.sweep()

            if app.swept+app.mines == app.height*app.width:
                app.game_over(None, win=True)

    def flag(self, _):  # The _ is an artifact of the <Button-3> binding
        """Flag and unflag, accordingly"""
        if self.clicked:
            pass
        elif self.flagged:
            app.flags -= 1
            self.image = GIF[0]
            self['image'] = self.image
            self.flagged = False

        else:
            app.flags += 1
            self.image = GIF['flag']
            self['image'] = self.image
            self.flagged = True
        app.score.update(app.mines-app.flags)

    def sweep(self):
        """Reveal all adjacent tiles with no nearby mines, plus neighbors"""
        for xy in self.adjacent:
            neighbor = app.get_tile(*xy)
            if not neighbor.clicked:
                neighbor.click()


class Mine(Tile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        self['image'] = GIF['mine']

        # Increment all nearby tiles' mine counters
        for xy in self.adjacent:
            app.get_tile(*xy).mines_nearby += 1

    def click(self):
        """Game over, and the fatal mine gets a red background"""
        if not self.flagged and not self.clicked:
            self.clicked = True
            self['bg'] = 'red'
            self.reveal(GIF['mine'], 'sunken')
            app.game_over(self)

    def reveal(self, icon, relief):
        self.clicked = True
        self['relief'] = relief
        self['image'] = icon


class Digit(tk.Label):
    def __init__(self, x=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update(x)

    def update(self, x):
#        self.x = x%10
#        self.image = tk.PhotoImage(file='t{}.gif'.format(self.x))
        self.x = x
        self['image'] = GIF['t'][self.x]


class Counter(tk.Frame):
    def __init__(self, num, bd=2, height=23, width=39, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.digits = []
        for i in range(3):
            self.digits.append(Digit(master=self))
            self.digits[i].grid(row=0, column=i)
        self.update(num)

#        self.icons=['t{}.gif'.format(self.hundreds),
#                    't{}.gif'.format(self.tens),
#                    't{}.gif'.format(self.ones)]

    def update(self, num):
        self.num = min(num, 999)
#        self.hundreds = num // 100
#        self.tens = (num % 100) // 10
#        self.ones = num % 10
#        self.nums = [self.hundreds, self.tens, self.ones]
        self.nums = [self.num // 100,  # Hundreds
                     (self.num % 100) // 10, # Tens
                     self.num % 10]  # Ones

        for d, x in zip(self.digits, self.nums):
            d.update(x)


class Clock(Counter):
    def start(self):
        self.t = threading.Timer(1.0, self.count)
        self.t.start()

    def count(self):
        self.num += 1
        self.update(self.num)
        print(threading.active_count())
        self.start()

    def stop(self):
        self.t.cancel()


app = App(root)
root.mainloop()
