
"""
This is a convenient container gathering all the main
search methods for the various database tables. 

It is intended to be used e.g. as 

> from src.utils import search
> match = search.objects(...)

Note that this is not intended to be a complete listing of all search
methods! You need to refer to the respective manager to get all
possible search methods. To get to the managers from your code, import
the database model and call its 'objects' property. 

Also remember that all commands in this file return lists (also if
there is only one match) unless noted otherwise.

Example: To reach the search method 'get_object_with_user' 
         in src/objects/managers.py:

> from src.objects.models import ObjectDB
> match = Object.objects.get_object_with_user(...)


"""

# Import the manager methods to be wrapped

from src.objects.models import ObjectDB
from src.players.models import PlayerDB
from src.scripts.models import ScriptDB
from src.comms.models import Msg, Channel
from src.help.models import HelpEntry
from src.permissions.models import PermissionGroup
from src.config.models import ConfigValue

#
# Search objects as a character
# 
# NOTE: A more powerful wrapper of this method
#  is reachable from within each command class
#  by using self.caller.search()! 
#
#    def object_search(self, character, ostring,
#                      global_search=False, 
#                      attribute_name=None):
#        """
#        Search as an object and return results.
#        
#        character: (Object) The object performing the search.
#        ostring: (string) The string to compare names against.
#                  Can be a dbref. If name is appended by *, a player is searched for.         
#        global_search: Search all objects, not just the current location/inventory
#        attribute_name: (string) Which attribute to search in each object.
#                                 If None, the default 'name' attribute is used.        
#        """

objects = ObjectDB.objects.object_search

#
# Search for players 
#
# NOTE: Most usually you would do such searches from
#   from inseide command definitions using 
#   self.caller.search() by appending an '*' to the 
#   beginning of the search criterion.
#
# def player_search(self, ostring):
#     """
#     Searches for a particular player by name or 
#     database id.
#
#     ostring = a string or database id.
#     """

players = PlayerDB.objects.player_search 

#
#   Searching for scripts
#
# def script_search(self, ostring, obj=None, only_timed=False):
#     """
#     Search for a particular script.
#        
#     ostring - search criterion - a script ID or key
#     obj - limit search to scripts defined on this object
#     only_timed - limit search only to scripts that run
#                  on a timer.         
#     """

scripts = ScriptDB.objects.script_search

#
# Searching for communication messages
#
#
# def message_search(self, sender=None, receiver=None, channel=None, freetext=None):    
#     """
#     Search the message database for particular messages. At least one 
#     of the arguments must be given to do a search. 
#
#     sender - get messages sent by a particular player
#     receiver - get messages received by a certain player
#     channel - get messages sent to a particular channel 
#     freetext - Search for a text string in a message. 
#                NOTE: This can potentially be slow, so make sure to supply
#                one of the other arguments to limit the search.                     
#     """        

messages = Msg.objects.message_search


#
# Search for Communication Channels
#
# def channel_search(self, ostring)
#     """
#     Search the channel database for a particular channel.
#
#     ostring - the key or database id of the channel.
#     """

channels = Channel.objects.channel_search

#
# Find help entry objects. 
#
# def search_help(self, ostring, help_category=None):
#     """
#     Retrieve a search entry object.
#
#     ostring - the help topic to look for
#     category - limit the search to a particular help topic
#     """

helpentries = HelpEntry.objects.search_help 

# 
# Search for a permission group
#  Note that the name is case sensitive.      
#
# def search_permissiongroup(self, ostring):
#     """
#     Find a permission group
#
#     ostring = permission group name (case sensitive)
#               or database dbref
#     """

permgroups = PermissionGroup.objects.search_permgroup

#
# Get a configuration value
# 
# OBS - this returns a unique value (or None),
#       not a list! 
#
# def config_search(self, ostring):
#     """
#     Retrieve a configuration value.

#     ostring - a (unique) configuration key
#     """

configvalue = ConfigValue.objects.config_search
