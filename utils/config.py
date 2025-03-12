import configparser
import os

class Config:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__))), 'config.ini')
        
        self.defaults = {
            'General': {
                'project_dit': os.path.expanduser('~/Documents/VideoSubAutomation'),
                'temp_dir': os.path.expanduser('~/Documents/AutoLipSync/temp'),
                'log_level': 'INFO',
            },
            'Premiere': {
                'executable_path': '',
                'script_dir': os.path.join(os.path.dirname(os.path.dirname(
                    os.path.dirname(__file__))), 'scripts/premiere_scripts'),
            },
            'Processing': {
                'max_threads': '4',
                'quality_preset': 'medium'
            }
        }

        self.load()

def load(self):
    # Config or create with defaults
    if os.path.exists(self.config_path):
        self.config.read(self.config_path)
    else:
        self.create_default_config()

def create_default_config(self):
    for section, options in self.defaults.items():
      if not self.config.has_section(section):
        self.config.add_section(section)
      for option, value in options.items():
        self.config.set(section, option, str(value))
    
    
    os.makedirs(self.get('General', 'project_dir'), exist_ok=True)
    os.makedirs(self.get('General', 'temp_dir'), exist_ok=True)

    self.save()

def get(self, section, option):
        return self.config[section][option]

def set(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

def save(self):
        with open(self.config_path, 'w') as f:
            self.config.write(f)