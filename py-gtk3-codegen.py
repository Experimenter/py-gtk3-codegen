import xml.dom.minidom as dom

class gtk_codegen():
    
    def collect_tags(self,xmlString):
        '''collect signal handlers and control objects from the xml file'''
        
        doc = dom.parseString(xmlString)
        
        tag_collection={}
        
        tag_collection['signalhandlers'] = \
            [signal.getAttribute('handler') for signal in doc.getElementsByTagName('signal')]
        
        tag_collection['controlobjects'] = \
            [object.getAttribute('id') for object in doc.getElementsByTagName('object')\
             if object.getAttribute('class') in \
             ['GtkEntry','GtkTextView','GtkComboBox','GtkComboBoxEntry','GtkProgressBar',\
              'GtkCheckbox','GtkRadioButton','GtkSpinButton','GtkCalendar','GtkToolBar',\
              'GtkStatusbar','GtkFileChooserButton','GtkFontButton','GtkHScale','GtkVScale']]
        
        return tag_collection
    
    def create_template(self,pyfile,xmlfile):
        '''create a template python file with the file name pyfile
        containing all events with their linking code
        and easy access names for control objects'''
        fileobj = open(pyfile,'w')
        
        
        # Init code for py file 
        initpy = "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk;"
        self.write_block(initpy,fileobj)
        
        # Fill template by Generating Classes for each Toplevel object
        for (topclass,topxml) in self.get_toplevelxml(xmlfile):
            # Fetch collected tags
            tags = self.collect_tags(topxml)
            initclass = 'class %s:;;+>def __init__( self ):;;' % topclass
            initclass += '+>self.builder = Gtk.Builder();self.builder.add_from_file("%s");' % xmlfile
            self.write_block(initclass,fileobj)
            
            # Easy Handlers for controlobjects
            control_handlers = ""
            for handler in tags['controlobjects'] :
                control_handlers+='self.%s=self.builder.get_object("%s");' % (handler,handler)
            self.write_block(control_handlers,fileobj,2)
            
            # Dictionary of events
            if len(tags['signalhandlers'])>0:
                dic_elements = 'dic={;+>'
                for signal in tags['signalhandlers']:
                    dic_elements+='"%s": self.%s,;' %(signal,signal)
                dic_elements+='<-};self.builder.connect_signals(dic);'
                self.write_block(dic_elements,fileobj,2)
            
            # Function defs for dictionary of events
            for signal in tags['signalhandlers']:
                self.write_block('def %s(self, widget, data=None):;+>pass;'%signal,fileobj,1)
        
        #finish pyfile
        self.write_block(';if __name__ ==\'__main__\':;+>#replace if %s is not the main class;'
                         '%s();Gtk.main()'% (topclass,topclass), fileobj)
        
        
    def get_toplevelxml(self,xmlfile):
        '''fetch toplevel objects like windows,applicationWindow,Dialog boxes etc.. '''
        layout = dom.parse(xmlfile)
        topobjects = [(object.getAttribute('id'),object.toxml()) \
            for object in layout.getElementsByTagName('object')\
            if object.getAttribute('class') in \
            ['GtkWindow','GtkApplicationWindow','GtkDialog','GtkAboutDialog']]
        return topobjects
        
       
        
    def write_block(self,text_block,file_object, initial_indent=0):
        '''Writes a block to the file with appropriate indentations 
        the following input strings effect intentation as follows 
        +> increases <- decreases <* reset to initial level
        and ; acts as a line terminator '''
        
        local_indent = 0
        blocklines = [lines.strip() for lines in text_block.split(';')]
        for line in blocklines:
            if line[:2] =='+>': local_indent+=1 
            if line[:2] =='<-' and local_indent > 0: local_indent-=1
            if line[:2] =='<*': local_indent = 0
            file_object.write(' '*4*(initial_indent+local_indent)+line.lstrip('+-<>* ')+'\n')
    
import sys
codegen = gtk_codegen()
if len(sys.argv)<=1:
    print ("usage: py-gtk3-codegen glade_file.xml [template.py]")
elif len(sys.argv)==2:
    #create file abc.py from abc.xml/abc.glade if name of py file is not provided
    codegen.create_template(sys.argv[1].split('.')[0]+'.py',sys.argv[1])
else:
    codegen.create_template(sys.argv[2],sys.argv[1])
