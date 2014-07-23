from gourmet.plugin import MainPlugin
import nutritionGrabberGui, nutrition
from gourmet.gglobals import add_icon
import os.path, gtk

class NutritionMainPlugin (MainPlugin):

    def activate (self, pluggable):
        """Setup nutritional database stuff."""
        add_icon(os.path.join(os.path.split(__file__)[0],'images','Nutrition.png'),
         'nutritional-info',
         _('Nutritional Information'))
        nutritionGrabberGui.check_for_db(pluggable.session)
        pluggable.nd = nutrition.NutritionData(pluggable.session,pluggable.conv)
        pluggable.rd.nd = pluggable.nd
