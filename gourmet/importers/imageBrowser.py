import threading
import time
import unittest

from gi.repository import GdkPixbuf, Gtk, Pango

from gourmet.image_utils import make_thumbnail
from gourmet.gtk_extras.dialog_extras import ModalDialog


class ImageBrowser(Gtk.IconView):
    def __init__ (self,*args,**kwargs):
        Gtk.IconView.__init__(self,*args,**kwargs)
        self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.set_model(self.model)
        self.set_pixbuf_column(0)
        self.image_queue = []
        self.progress_queue = []
        self.to_add_lock = threading.Lock()
        self.updating = False
        self.adding = []
        self.alive = False
        GObject.timeout_add(100,self.update_progress)
        GObject.timeout_add(100,self.add_image_from_queue)

    def add_image_from_uri (self, u, progress_portion=1, progress_start_at=0):
        self.to_add_lock.acquire()
        self.adding.append({'url':u,
                            'progress_portion':progress_portion,
                            'progress_start_at':progress_start_at,
                            }
                           )
        self.to_add_lock.release()
        if not self.alive:
            self.run_thread()

    def quit (self):
        self.alive = False

    def run_thread (self):
        self.alive = True
        t=threading.Thread(target=self.fetch_images)
        t.start()

    def fetch_images (self):
        while self.alive:
            if self.adding:
                self.to_add_lock.acquire()
                to_add = self.adding[0]; self.adding = self.adding[1:]
                self.to_add_lock.release()
                make_thumbnail(to_add['url'],
                               'small',
                               self.image_queue,
                    self.progress_queue,
                    progress_portion=to_add['progress_portion'],
                    progress_start_at=to_add['progress_start_at']
                    )
            else:
                time.sleep(0.1)

    def add_image_from_queue (self):
        try:
            fi,u = self.image_queue.pop()
            if fi:
                pb = GdkPixbuf.Pixbuf.new_from_file(fi)
                self.model.append([pb,u])
        except IndexError:
            pass
        return True

    def update_progress (self):
        try:
            text,progress = self.progress_queue.pop()
            #print 'Set progress',progress,text
            self.prog = progress,text
            self.set_progress(float(progress),text)
            #print 'UPDATE_PROGRESS',time.time(),progress,text
        except IndexError:
            if not self.adding and hasattr(self,'progressbar'):
                self.progressbar.hide()
            #elif hasattr(self,'progressbar'):
            #    self.progressbar.pulse()
        else:
            if progress == 1:
                print('Done!')
                self.progressbar.hide()
                return None
        return True

    def set_progress (self, progress, text):
        if hasattr(self, 'progressbar'):
            self.progressbar.show()
            self.progressbar.set_percentage(progress)
            self.progressbar.set_text(text)


class ImageBrowserDialog (ModalDialog):
    def __init__ (self, default=None, title="Select Image",okay=True,
                  label="Select an image", sublabel=None,parent=None, cancel=True, modal=True, expander=None):
        ModalDialog.__init__(self,default=default, title=title,
                             okay=okay,label=label,sublabel=sublabel,
                             parent=parent, cancel=cancel, modal=modal,
                             expander=expander)
        self.set_default_size(600,600)

    def setup_dialog (self, *args, **kwargs):
        ModalDialog.setup_dialog(self,*args,**kwargs)
        self.ib = ImageBrowser()
        self.ib.connect('selection-changed',self.selection_changed_cb)
        self.ib.connect('item-activated',self.okcb)
        self.sw = Gtk.ScrolledWindow()
        self.pb = Gtk.ProgressBar(); self.pb.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.vbox.pack_end(self.sw, True, True, 0)
        self.vbox.pack_end(self.pb,expand=False)
        self.ib.progressbar = self.pb
        self.sw.add(self.ib)
        self.sw.show_all()
        self.sw.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)

    def okcb (self, *args,**kwargs):
        self.ib.quit()
        ModalDialog.okcb(self,*args,**kwargs)


    def selection_changed_cb (self, iv):
        selected_paths = iv.get_selected_items()
        if selected_paths:
            itr = self.ib.model.get_iter(selected_paths[0])
            val = self.ib.model.get_value(itr,1)
            self.ret = val
        else:
            self.ret = None

    def add_images_from_uris_w_progress (self, uris):
        prog_perc = 1.0 / len(uris)
        for n,u in enumerate(uris):
            self.ib.add_image_from_uri(
                u,
                progress_portion=prog_perc,
                progress_start_at=prog_perc*n
                )

    def add_image_from_uri (self, u):
        self.ib.add_image_from_uri(u)

class ImageBrowserTest (unittest.TestCase):

    def setUp (self):
        self.ib = ImageBrowser()
        self.w = Gtk.Window()
        self.sw = Gtk.ScrolledWindow()
        self.sw.add(self.ib)
        self.sw.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
        self.w.add(self.sw)

    #def testWindow (self):
    #    self.w.show_all()
    #    self.ib.show_all()
    #    for image in ['Caneel beach.JPG','Cinnamon beach.JPG','dsc00258.jpg']:
    #        self.ib.add_image_from_uri('file:///home/tom/pictures/'+image)
    #    self.ib.add_image_from_uri('http://wikipes.com/wikipes-logo.gif')
    #    self.w.connect('delete-event',lambda *args: Gtk.main_quit())
    #    Gtk.main()

    def testDialog (self):
        self.ibd = ImageBrowserDialog()
        self.ibd.add_images_from_uris_w_progress(
            ['http://ideasinfood.typepad.com/ideas_in_food/images/katzs_pastrami_reuben.jpg'] \
#            + ['file:///home/tom/pictures/'+image for image in ['Caneel beach.JPG','Cinnamon beach.JPG','dsc00258.jpg']]
            )
        #for image in []:
        #    self.ibd.add_image_from_uri()
        import os
        if os.name!='nt':
            Gtk.threads_init()
        self.ibd.run()


if __name__ == '__main__':
    try:
        # Make unit test not run from emacs C-c C-c into python shell...
        __file__
        print('UNITTEST')
        unittest.main()
    except:
        pass


