import tkinter as tk
from tkinter import filedialog as fd
from tkinter import simpledialog as sd
from tkinter import messagebox as mesbox
import matplotlib as mpl
mpl.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import gprpy as gp
import numpy as np
import toolbox.splash as splash
import os
import Pmw
import scipy.interpolate as interp



colsp=2
rightcol=10
halfwid=4
figrowsp=15+1

class GPRPyCWApp:

    def __init__(self,master):
        self.window = master

        master.title("GPRPy CW")

        self.balloon = Pmw.Balloon()
        fig = Figure(figsize=(9,5))
        ahyp = fig.add_axes([0.065,0.1,0.27,0.83])
        alin = fig.add_axes([0.365,0.1,0.27,0.83])
        adata= fig.add_axes([0.665,0.1,0.27,0.83])
        #adata.get_yaxis().set_visible(False)
        alin.get_yaxis().set_visible(False)

        mpl.rcParams.update({'font.size': mpl.rcParams['font.size']*1.1})
        ahyp.tick_params(direction='out',length=6,width=1)
        alin.tick_params(direction='out',length=6,width=1)
        adata.tick_params(direction='out',length=6,width=1)
        
        adata.set_title('data')
        adata.get_yaxis().tick_right()
        adata.get_yaxis().set_label_position('right')
        adata.set_ylabel('two-way travel time [ns]', fontsize=mpl.rcParams['font.size'])
        
        alin.set_title('linear semblance')
        ahyp.set_title('hyperbolic semblance')
        ahyp.set_ylabel('two-way travel time [ns]', fontsize=mpl.rcParams['font.size'])        
        
        canvas = FigureCanvasTkAgg(fig, master=self.window)
        canvas.get_tk_widget().grid(row=2,column=0,columnspan=rightcol,rowspan=figrowsp,sticky='nsew')
        canvas.draw()

        self.vmin = 0.01
        self.vmax = 0.33
        self.vint = 0.005

        self.showlnhp = False
        
        proj = gp.gprpyCW()



        ## Data processing buttons
        
        # Load data
        LoadButton = tk.Button(
            text="import data", fg="black",
            command=lambda : [self.loadData(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        LoadButton.config(height = 1, width = 2*halfwid)         
        LoadButton.grid(row=0, column=rightcol, sticky='nsew',columnspan=colsp,rowspan=2)


        # Adjust profile length; if trigger wheel is not good
        AdjProfileButton = tk.Button(
            text="adj profile", fg="black",
            command=lambda : [self.adjProfile(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        AdjProfileButton.config(height = 1, width = 2*halfwid)         
        AdjProfileButton.grid(row=2, column=rightcol, sticky='nsew',columnspan=colsp)
        self.balloon.bind(AdjProfileButton,
                          "Adjust the profile length to \n"
                          "known start and end positions.")


        # Set new zero time
        SetZeroTimeButton = tk.Button(
            text="set zero time", fg="black",
            command=lambda : [self.setZeroTime(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        SetZeroTimeButton.config(height = 1, width = 2*halfwid)         
        SetZeroTimeButton.grid(row=3, column=rightcol, sticky='nsew',columnspan=colsp)    
        self.balloon.bind(SetZeroTimeButton,
                          "Set the two-way travel time that \n" 
                          "that corresponds to the surface.")

        # truncate Y
        truncYButton = tk.Button(
            text="truncate Y", fg="black",
            command=lambda : [self.truncateY(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        truncYButton.config(height = 1, width = 2*halfwid)         
        truncYButton.grid(row=4, column=rightcol, sticky='nsew',columnspan=colsp)
        self.balloon.bind(truncYButton,
                          "Remove data points at arrival times\n"
                          "later than the chosen value. If velocity\n"
                          "is given: remove data points at depths greater\n"
                          "than the chosen value")   


        # Dewow
        DewowButton = tk.Button(
            text="dewow", fg="black",
            command=lambda : [self.dewow(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        DewowButton.config(height = 1, width = 2*halfwid)         
        DewowButton.grid(row=5, column=rightcol, sticky='nsew',columnspan=colsp)
        self.balloon.bind(DewowButton,
                          "Trace-wise low-cut filter. Removes\n" 
                          "from each trace a running mean of\n"
                          "chosen window width.") 


        # Smooth 
        SmoothButton = tk.Button(
            text="smooth", fg="black",
            command=lambda : [self.smooth(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        SmoothButton.config(height = 1, width = 2*halfwid)         
        SmoothButton.grid(row=6, column=rightcol, sticky='nsew',columnspan=colsp)
        self.balloon.bind(SmoothButton,
                          "Trace-wise high-cut filter. Replaces\n" 
                          "each sample within a trace by a\n"
                          "running mean of chosen window width.")
        
        
        # Normalize
        NormalizeButton = tk.Button(
            text="normalize", fg="black",
            command = lambda : [proj.normalize(),
                                self.plotCWData(proj,a=adata,canvas=canvas)])
        NormalizeButton.config(height = 1, width = 2*halfwid)         
        NormalizeButton.grid(row=7, column=rightcol, sticky='nsew',columnspan=colsp)
        self.balloon.bind(NormalizeButton,
                          "Normalizes each trace such that\n" 
                          "they all have equal energy") 


        # Gain
        tpowButton = tk.Button(
            text="tpow", fg="black",
            command=lambda : [self.tpowGain(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        tpowButton.config(height=1, width=halfwid)
        tpowButton.grid(row=8, column=rightcol, sticky='nsew')
        self.balloon.bind(tpowButton,
                          "t-power gain. Increases the power of the\n"
                          "signal by a factor of (two-way travel time)^p,\n"
                          "where the user provides p. This gain is often\n" 
                          "less aggressive than agc.")

        
        agcButton = tk.Button(
            text="agc",fg="black",
            command=lambda : [self.agcGain(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        agcButton.config(height=1, width=halfwid)
        agcButton.grid(row=8, column=rightcol+1, sticky='nsew')
        self.balloon.bind(agcButton,
                          "Automatic gain controll. Normalizes the power\n"
                          "of the signal per given sample window along\n" 
                          "each trace.")

        
        # Lin Semblance
        LinSembButton = tk.Button(
            text="lin semb", fg="black",
            command = lambda : [self.linSemb(proj),
                                self.plotSemb(proj,a=alin,canvas=canvas,
                                              semb=proj.linSemb,title='linear semblance')])
        LinSembButton.config(height = 1, width = 2*halfwid)
        LinSembButton.grid(row=9, column=rightcol, sticky='nsew',columnspan=colsp)

        
        # Hyp Semblance
        HypSembButton = tk.Button(
            text="hyp semb", fg="black",
            command = lambda : [self.hypSemb(proj),
                                self.plotSemb(proj,a=ahyp,canvas=canvas,
                                              semb=proj.hypSemb,
                                              title='hyperbolic semblance',
                                              ylabel='two-way travel time [ns]')])
        HypSembButton.config(height = 1, width = 2*halfwid)
        HypSembButton.grid(row=10, column=rightcol, sticky='nsew',columnspan=colsp)

        # Add line on top of data
        AddLinButton = tk.Button(
            text="add ln", fg="black",
            command = lambda : [self.addLin(proj),
                                self.plotCWData(proj,a=adata,canvas=canvas)])
        AddLinButton.config(height = 1, width = halfwid)
        AddLinButton.grid(row=11,column=rightcol, sticky='nsew')
        
        # Draw hyperbola on top of data
        AddHypButton = tk.Button(
            text="add hp", fg="black",
            command = lambda : [self.addHyp(proj),
                                self.plotCWData(proj,a=adata,canvas=canvas)])
        AddHypButton.config(height = 1, width = halfwid)
        AddHypButton.grid(row=11,column=rightcol+1, sticky='nsew')


        # Remove most recent line
        RemLinButton = tk.Button(
            text="rem ln", fg="black",
            command = lambda : [proj.remLin(),
            self.plotCWData(proj,a=adata,canvas=canvas)])
        RemLinButton.config(height = 1, width = halfwid)
        RemLinButton.grid(row=12,column=rightcol, sticky='nsew')

        # Remove most recent hyperbola
        RemHypButton = tk.Button(
            text="rem hp", fg="black",
            command = lambda : [proj.remHyp(),
            self.plotCWData(proj,a=adata,canvas=canvas)])
        RemHypButton.config(height = 1, width = halfwid)
        RemHypButton.grid(row=12,column=rightcol+1, sticky='nsew')

                          
        
        # Show ln hp toggle
        ShowLnHpButton = tk.Button(
            text="show ln/hp", fg="black",
            command = lambda : [self.toggleLnHp(),
                                self.plotCWData(proj,a=adata,canvas=canvas)])
        ShowLnHpButton.config(height = 1, width = 2*halfwid)
        ShowLnHpButton.grid(row=13,column=rightcol, sticky='nsew',columnspan=colsp)
        

        # Print figure
        PrintFigButton = tk.Button(
            text="print figure", fg="black",
            command = lambda : [self.printFigures(proj,fig)])
        PrintFigButton.config(height = 1, width = 2*halfwid)
        PrintFigButton.grid(row=14,column=rightcol, sticky='nsew',columnspan=colsp)

        
        # Write script
        HistButton = tk.Button(
            text="write script", fg="black",
            command=lambda : self.writeHistory(proj))
        HistButton.config(height = 1, width = 2*halfwid)         
        HistButton.grid(row=15, column=rightcol, sticky='nsew',columnspan=colsp)
        self.balloon.bind(HistButton,
                          'Writes a python script to reproduce the current \n'
                          'status as a\n'
                          '\n'
                          'If the current data is from a .gpr file, \n'  
                          'then the python script will contain all \n'
                          'steps going back to the raw data. \n'
                          '\n'
                          'The script will not contain visualization \n'
                          'settings such as x-range settings, unless \n'
                          'the "print figure" command was used. ')




        
        ## Visualization buttons

        # Undo Button
        undoButton = tk.Button(
            text="undo",
            command=lambda : [proj.undo(),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        undoButton.config(height = 1, width = 2*halfwid)
        undoButton.grid(row=0, column=0, sticky='nsew',rowspan=2)
        self.balloon.bind(undoButton,
                          '"Undoes" the most recent processing step and\n' 
                          'sets the data back to its previous state.\n' 
                          'This also removes the most recent processing\n'
                          'step from the history. Does not revert\n' 
                          'visualization settings such as "set x-range"\n'
                          'etc.')


        # Full view
        FullButton = tk.Button(
            text="full view", fg="black",
            command=lambda : [self.setFullView(proj),
                              self.plotCWData(proj,a=adata,canvas=canvas),
                              self.plotSemb(proj,a=alin,canvas=canvas,semb=proj.linSemb,title='linear semblance'),
                              self.plotSemb(proj,a=ahyp,canvas=canvas,semb=proj.hypSemb,
                                            title='hyperbolic semblance',ylabel='two-way travel time [ns]')])
        FullButton.config(height = 1, width = 2*halfwid)         
        FullButton.grid(row=0, column=1, sticky='nsew',rowspan=2)
        self.balloon.bind(FullButton,"Resets x- and y-axis limits to full data.")

        
        # Saturation
        sattext = tk.StringVar()
        sattext.set("semblance sat")
        satlabel = tk.Label(master, textvariable=sattext,height = 1,width = 4*halfwid)
        satlabel.grid(row=0, column=2, sticky='nsew')
        self.balloon.bind(satlabel,"Semblance color saturation")
        self.saturation = tk.DoubleVar()
        satbox = tk.Entry(master, textvariable=self.saturation, width=4*halfwid)
        satbox.grid(row=1, column=2, sticky='nsew')
        self.saturation.set("1.0")

        # Lin or log mode switch for semblance representation
        self.sembrep=tk.StringVar()
        self.sembrep.set("lin")
        repswitch = tk.OptionMenu(master,self.sembrep,"lin","log")
        repswitch.grid(row=0, column=3, sticky='nsew',rowspan=2)
        self.balloon.bind(repswitch,
                          "Choose between linear\n"
                          "and logarithmic scale\n" 
                          "for semblance colors.")

        
         # Set velocity range
        VelrngButton = tk.Button(
            text="set vel range", fg="black",
            command=lambda : [self.setVelRng()])
        VelrngButton.config(height = 1, width = 2*halfwid)         
        VelrngButton.grid(row=0, column=4, sticky='nsew',rowspan=2)
        self.balloon.bind(VelrngButton,"Set the velocity range\n"
                                       "used in the semblance\n"
                                       "analysis.")
        
        # X range
        XrngButton = tk.Button(
            text="set x-range", fg="black",
            command=lambda : [self.setXrng(),
                              self.plotCWData(proj,a=adata,canvas=canvas)])
        XrngButton.config(height = 1, width = 2*halfwid)         
        XrngButton.grid(row=0, column=5, sticky='nsew',rowspan=2)
        self.balloon.bind(XrngButton,"Set the x-axis display limits.")
        
        
        # Y range
        YrngButton = tk.Button(
            text="set y-range", fg="black",
            command=lambda : [self.setYrng(),
                              self.plotCWData(proj,a=adata,canvas=canvas),
                              self.plotSemb(proj,a=alin,canvas=canvas,semb=proj.linSemb,title='linear semblance'),
                              self.plotSemb(proj,a=ahyp,canvas=canvas,semb=proj.hypSemb,
                                            title='hyperbolic semblance',ylabel='two-way travel time [ns]')])
        YrngButton.config(height = 1, width = 2*halfwid)         
        YrngButton.grid(row=0, column=6, sticky='nsew',rowspan=2)
        self.balloon.bind(YrngButton,"Set the y-axis display limits.")

        
        
        # Contrast
        contrtext = tk.StringVar()
        contrtext.set("contrast")
        contrlabel = tk.Label(master, textvariable=contrtext,height = 1,width = 2*halfwid)
        contrlabel.grid(row=0, column=7, sticky='nsew')
        self.balloon.bind(contrlabel,"Data color saturation")
        self.contrast = tk.DoubleVar()
        contrbox = tk.Entry(master, textvariable=self.contrast, width=2*halfwid)
        contrbox.grid(row=1, column=7, sticky='nsew')
        self.contrast.set("1.0")

        
        # Mode switch for figure color
        self.color=tk.StringVar()
        self.color.set("gray")
        colswitch = tk.OptionMenu(master,self.color,"gray","bwr")
        colswitch.grid(row=0, column=8, sticky='nsew',rowspan=2)
        self.balloon.bind(colswitch,
                          "Choose between gray-scale\n"
                          "and red-white-blue (rwb)\n" 
                          "data representation.")


        
        # Refreshing plot
        plotButton = tk.Button(
            text="refresh plot",
            command=lambda : [self.plotCWData(proj,a=adata,canvas=canvas),
                              self.plotSemb(proj,a=alin,canvas=canvas,semb=proj.linSemb,title='linear semblance'),
                              self.plotSemb(proj,a=ahyp,canvas=canvas,semb=proj.hypSemb,
                                            title='hyperbolic semblance',ylabel='two-way travel time [ns]')])
        plotButton.config(height = 1, width = 2*halfwid)
        plotButton.grid(row=0, column=9, sticky='nsew',rowspan=2)
        self.balloon.bind(plotButton,
                          "Refreshes the figure after changes\n"
                          "in the visualization settings. Also\n"
                          "removes any plotted hyperbolae.")




        
        

    # functions

    
    def loadData(self,proj):
        filename = fd.askopenfilename( filetypes= (("All", "*.*"),
                                                   ("Sensors and Software (.DT1)", "*.DT1"),
                                                   ("GSSI (.DZT)", "*.DZT")))
        if filename:
            self.getType()
            if self.dtype is not None:
                proj.importdata(filename,self.dtype)
                self.xrng = [np.min(proj.profilePos),np.max(proj.profilePos)]
                self.yrng = [0,np.max(proj.twtt)]
           

    def getType(self):
        typeQuery = tk.Toplevel(self.window)
        typeQuery.title("Data type")
        text = tk.Label(typeQuery,text="Is this a common midpoint (CMP) or\n"
                        "wide aperture reflection and refraction (WARR)\n"
                        "data set?",fg="red")
        text.pack(padx=10,pady=10)
        CMPButton = tk.Button(typeQuery, text="CMP", width=10,
                              command = lambda : [self.setCMP(),
                                                  typeQuery.destroy()])
        CMPButton.pack(side="left")
        WARRButton = tk.Button(typeQuery, text="WARR", width=10,
                               command = lambda : [self.setWARR(),
                                                   typeQuery.destroy()])
        WARRButton.pack(side="right")
        # This forces the program to wait until this query is answered
        self.window.wait_window(typeQuery) 
    def setCMP(self):
        self.dtype = 'CMP'
        print("Data type is CMP")
    def setWARR(self):
        self.dtype = 'WARR'
        print("Data type is WARR")


    def setFullView(self,proj):
        self.xrng=[np.min(proj.profilePos),np.max(proj.profilePos)]
        self.yrng=[np.min(proj.twtt),np.max(proj.twtt)]
                

    def plotCWData(self,proj,a,canvas):
        a.clear()
        dx=proj.profilePos[1]-proj.profilePos[0]
        dt=proj.twtt[1]-proj.twtt[0]
        stdcont = np.nanmax(np.abs(proj.data)[:])
        a.imshow(proj.data,cmap=self.color.get(),extent=[min(proj.profilePos)-dx/2.0,
                                                         max(proj.profilePos)+dx/2.0,
                                                         max(proj.twtt)+dt/2.0,
                                                         min(proj.twtt)-dt/2.0],
                 aspect="auto",
                 vmin=-stdcont/self.contrast.get(), vmax=stdcont/self.contrast.get())
        a.set_ylim(self.yrng)
        a.set_xlim(self.xrng)
        a.invert_yaxis()
        if self.dtype == "WARR":
            a.set_xlabel("antenna separation [m]", fontsize=mpl.rcParams['font.size'])
        elif self.dtype == "CMP":
            a.set_xlabel("distance from midpoint [m]", fontsize=mpl.rcParams['font.size'])
        a.set_title('data')
        a.set_ylabel('two-way travel time [ns]', fontsize=mpl.rcParams['font.size'])
        a.get_xaxis().set_ticks_position('both')
        a.get_yaxis().set_ticks_position('both')
        # If we have any hyperbolae or lines, we need to plot them too:
        if proj.dtype is "WARR":
            typefact = 1
        elif proj.dtype is "CMP":
            typefact = 2
        if self.showlnhp:            
            if proj.lins:
                for lin in proj.lins:
                    time = lin[0] + typefact*proj.profilePos/lin[1]
                    a.plot(proj.profilePos,time,linewidth=2,color='yellow')
                    a.plot(proj.profilePos,time,linewidth=1,color='black')
            if proj.hyps:
                x2 = np.power(typefact*proj.profilePos,2.0)
                for hyp in proj.hyps:
                    time = np.sqrt(x2 + 4*np.power(hyp[0]/2.0 * hyp[1],2.0))/hyp[1]
                    a.plot(proj.profilePos,time,linewidth=2,color='yellow')
                    a.plot(proj.profilePos,time,linewidth=1,color='black')
                

        # Allow for cursor coordinates being displayed        
        def pressed(event):
            if event.xdata is not None and event.ydata is not None:
                canvas.get_tk_widget().itemconfigure(tag, text="(x = %5.5g, y = %5.5g)" % (event.xdata, event.ydata))
                
        canvas.mpl_connect('button_press_event', pressed)        

        #tag = canvas.get_tk_widget().create_text(620, -2, text="", anchor="nw")
        tag = canvas.get_tk_widget().create_text(2, -3, text="", anchor="nw")
        
        canvas.get_tk_widget().grid(row=2,column=0,columnspan=rightcol, rowspan=15, sticky='nsew')
        canvas.draw()

        
    def plotSemb(self,proj,a,canvas,semb,title,ylabel=None):
        dt=proj.twtt[1]-proj.twtt[0]
        if semb is not None:
            dv=proj.vVals[1]-proj.vVals[0]
            a.clear()
            if self.sembrep.get() == "lin":
                #print("Linear semblance representation")
                stdcont = np.nanmax(np.abs(semb)[:])
                a.imshow(np.flipud(np.abs(semb)), cmap='inferno',
                         extent=[np.min(proj.vVals)-dv/2.0, np.max(proj.vVals)+dv/2.0,
                                 np.min(proj.twtt)-dt/2.0,  np.max(proj.twtt)+dt/2.0],
                         aspect='auto',
                         vmin=0, vmax=stdcont/self.saturation.get())
            elif self.sembrep.get() == "log":
                #print("Logarithmic semblance representation")
                stdcont = np.nanmax(np.log(np.abs(semb))[:])
                a.imshow(np.flipud(np.log(np.abs(semb))), cmap='inferno',
                         extent=[np.min(proj.vVals)-dv/2.0, np.max(proj.vVals)+dv/2.0,
                                 np.min(proj.twtt)-dt/2.0,  np.max(proj.twtt)+dt/2.0],
                         aspect='auto',
                         vmin=0, vmax=stdcont/self.saturation.get())
            elif self.sembrep.get() == "exp":
                #print("Exponential semblance representation")
                stdcont = np.nanmax(np.exp(np.abs(semb))[:])
                a.imshow(np.flipud(np.exp(np.abs(semb))), cmap='inferno',
                         extent=[np.min(proj.vVals)-dv/2.0, np.max(proj.vVals)+dv/2.0,
                                 np.min(proj.twtt)-dt/2.0,  np.max(proj.twtt)+dt/2.0],
                         aspect='auto',
                         vmin=0, vmax=stdcont/self.saturation.get())

                
            a.set_ylim(self.yrng)
            a.set_xlabel("velocity [m/ns]", fontsize=mpl.rcParams['font.size'])
            a.invert_yaxis()
            a.set_title(title)
            a.get_xaxis().set_ticks_position('both')
            a.get_yaxis().set_ticks_position('both')
            if ylabel is not None:
                a.set_ylabel(ylabel, fontsize=mpl.rcParams['font.size'])            
        
            def pressed(event):
                if event.xdata is not None and event.ydata is not None:
                    canvas.get_tk_widget().itemconfigure(tag, text="(x = %5.5g, y = %5.5g)" % (event.xdata, event.ydata))
                
            canvas.mpl_connect('button_press_event', pressed)
            tag = canvas.get_tk_widget().create_text(2, -3, text="", anchor="nw")
        
        
            canvas.get_tk_widget().grid(row=2,column=0,columnspan=rightcol, rowspan=15, sticky='nsew')
            canvas.draw()


        
    def setYrng(self):
        ylow = sd.askfloat("Input","Min Y value")
        if ylow is not None:            
            yhigh = sd.askfloat("Input","Max Y value")
            if yhigh is not None:
                self.prevyrng=self.yrng
                self.yrng=[ylow,yhigh]


    def setXrng(self):
        xlow = sd.askfloat("Input","Min X value")
        if xlow is not None:
            xhigh = sd.askfloat("Input","Max X value")
            if xhigh is not None:
                self.xrng=[xlow,xhigh]

    def setVelRng(self):
        vmin = sd.askfloat("Input","Minimum velocity")
        if vmin is not None:
            self.vmin = vmin
        vmax = sd.askfloat("Input","Maximum velocity")
        if vmax is not None:
            self.vmax = vmax
        vint = sd.askfloat("Input","Velocity step size (interval)")
        if vint is not None:
            self.vint = vint    
            

    def adjProfile(self,proj):
        minPos = sd.askfloat("Input","Start x coordinate")
        if minPos is not None:
            maxPos = sd.askfloat("Input","End x coordinate")
            if maxPos is not None:
                proj.adjProfile(minPos=minPos,maxPos=maxPos)
                self.xrng=[minPos,maxPos]

                
    def setZeroTime(self,proj):
        newZeroTime = sd.askfloat("Input","New zero time")
        if newZeroTime is not None:
            proj.setZeroTimeCW(newZeroTime=newZeroTime)


    def truncateY(self,proj):
        maxY = sd.askfloat("Input","Maximum two-way travel time?")
        if maxY is not None:
            proj.truncateY(maxY)

    def dewow(self,proj):
        window = sd.askinteger("Input","Dewow window width (number of samples)")
        if window is not None:
            proj.dewow(window=window)

    def smooth(self,proj):
        window = sd.askinteger("Input",
                               "Smoothing window width (number of samples)")
        if window is not None:
            proj.smooth(window=window)            
            
    def tpowGain(self,proj):
        power = sd.askfloat("Input","Power for tpow gain?")
        if power is not None:
            proj.tpowGain(power=power)

    def agcGain(self,proj):
        window = sd.askinteger("Input","Window length for AGC?")
        if window is not None:
            proj.agcGain(window=window)

            
    def linSemb(self,proj):
        proj.linSemblance(self.vmin,self.vmax,self.vint)

    def hypSemb(self,proj):
        proj.hypSemblance(self.vmin,self.vmax,self.vint)
        

    def addLin(self,proj):
        self.showlnhp = True
        vel = sd.askfloat("Input","Velocity?")
        if vel is not None:
            zerotwtt = sd.askfloat("Input","Zero two-way travel time?")
            if zerotwtt is not None:           
                proj.addLin(zerotwtt=zerotwtt,vel=vel)


    def addHyp(self,proj):
        self.showlnhp = True
        vel = sd.askfloat("Input","Velocity?")
        if vel is not None:            
            zerotwtt = sd.askfloat("Input","Zero two-way travel time?")
            if zerotwtt is not None:
                proj.addHyp(zerotwtt=zerotwtt,vel=vel)                                

                
    def toggleLnHp(self):
        self.showlnhp = not self.showlnhp


    def printFigures(self,proj,fig):
        dpi=None
        # Make combined figure
        figname = fd.asksaveasfilename(defaultextension=".pdf",
                                       title="Filename for figures")
        if figname is not '':
            fignamesplit=os.path.splitext(figname)
            dpi = sd.askinteger("Input","Resolution in dots per inch? (Recommended: 600)")
            if dpi is not None:
                fig.savefig(figname, format='pdf', dpi=dpi)
                print('Printed %s' %(figname))
                # Also create individual figures
                proj.printCWFigure(fignamesplit[0]+"_data"+fignamesplit[1], color=self.color.get(),
                                   contrast=self.contrast.get(),
                                   yrng=self.yrng, xrng=self.xrng,
                                   dpi=dpi, showlnhp=self.showlnhp)                
                print('Printed %s' %(fignamesplit[0]+"_data"+fignamesplit[1]))
                
                if proj.linSemb is not None:
                     proj.printSembFigure(fignamesplit[0]+"_linSemb"+fignamesplit[1], whichsemb="lin",
                                          saturation=self.saturation.get(),
                                          yrng=self.yrng, vrng=[self.vmin,self.vmax],
                                          sembrep=self.sembrep.get(),
                                          dpi=dpi)
                     print('Printed %s' %(fignamesplit[0]+"_linSemb"+fignamesplit[1]))
                     
                if proj.hypSemb is not None:
                     proj.printSembFigure(fignamesplit[0]+"_hypSemb"+fignamesplit[1], whichsemb="hyp",
                                          saturation=self.saturation.get(),
                                          yrng=self.yrng, vrng=[self.vmin,self.vmax],
                                          sembrep=self.sembrep.get(),
                                          dpi=dpi)
                     print('Printed %s' %(fignamesplit[0]+"_hypSemb"+fignamesplit[1]))
                
    def writeHistory(self,proj):        
        filename = fd.asksaveasfilename(defaultextension=".py")
        if filename is not '':
            proj.writeHistory(filename)
            print("Wrote history to " + filename)
            
            
         
root = tk.Tk()

#root.columnconfigure(0, weight=1)
#root.rowconfigure(0, weight=1)

for col in range(rightcol):
    root.columnconfigure(col, weight=1)
for row in range(figrowsp):    
    root.rowconfigure(row, weight=1)

app = GPRPyCWApp(root)

root.mainloop()
