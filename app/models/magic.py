import random
import xml.etree.ElementTree as ET

##########################################
#      Spell and Character Elements      #
##########################################
# Default Element class.
class Element(object):
    # Initialize a new element object
    def __init__(self, name, strong, weak, compatible):
        self.name = name
        self.strong = strong
        self.weak = weak
        self.compatible = compatible

    # Determine whether or not this element is roughly synonymous
    # With any other element.
    def is_compatible_with(self, element):
        return element.name in self.compatible

    # Return whether or not we will do extra damage to the input element
    def is_strong_against(self, element):
        return element.name in self.strong

    # Weak against does not mean elements that do extra damage to us
    # It means elements against which we do poor damage. There is a difference!
    def is_weak_against(self, element):
        return element.name in self.weak

##########################################
#             Spell Effects              #
##########################################

# How a particular spell will affect a targeted enemy
# Stats targeted, additional modifiers, etc.
class Effect(object):
    def __init__(self, element, power, accuracy=100):
        self.power = power
        self.element = element
        self.accuracy = accuracy

    def target_evades(self, caster, target):
        # Get respective target speeds
        evasion  = target.get_stat('speed')
        accuracy = caster.get_stat('speed')

        # Compute accuracy modifier based on difference in speeds
        modifier = float(accuracy - evasion)/max(1,float(accuracy+evasion))
        modifier = int(modifier*caster.modifier_minmax)
        modifier = float(max(2, 2 + modifier))/max(2, 2 - modifier)

        # Computer overall accuracy and test for hit using random variable
        accuracy = min(100, self.accuracy * modifier)
        return random.randint(0, 100) > accuracy

    def apply_effect(self, caster, target):
        raise NotImplementedError

# A spell which reduces the targets health. Damage is a function of
# attack power, caster power, target defense and some random variables
class AttackEffect(Effect):
    def __init__(self, element, power, accuracy, critical_hit_prob):
        # Call the parent Effect constructor first
        super(AttackEffect, self).__init__(element, power, accuracy)

        # Store move accuracy and critical hit probability
        self.critical_hit_prob = critical_hit_prob

    def compute_damage(self, caster, target, critical_hit=False):
        if critical_hit:
            print("Critical hit")
            # Critical hits ignore positive defense modifiers and negative attack modifiers
            attack = max(caster.get_stat('attack'), caster.get_base_stat('attack'))
            defense = min(target.get_stat('defense'), target.get_base_stat('defense'))
        else:
            attack = caster.get_stat('attack')
            defense = target.get_stat('defense')

        damage = 2 * attack * self.power//max(1,defense)
        damage = damage//25
        damage += 2

        if self.element.is_strong_against(target.element):
            print("It's super effective")
            damage *= 2
        elif self.element.is_weak_against(target.element):
            print("It's not very effective")
            damage //= 2

        if critical_hit:
            damage *= 2

        return damage

    # Simple computation of critical hit depending on critical_hit_prob of spell
    def is_critical_hit(self):
        return random.randint(0, 100) < self.critical_hit_prob

    # Override parent apply effect method for our AttackEffect
    def apply_effect(self, caster, target):
        summary = {
            "type"               : "attack",
            "super_effective"    : self.element.is_strong_against(target.element),
            "not_very_effective" : self.element.is_weak_against(target.element),
            "target" : target,
            "evades" : False
        }
        # Test for evasion and report if target dodged
        if self.target_evades(caster, target):
            summary["evades"] = True
            summary["sustained"] = 0
            print("{} evades the attack.".format(target.name))
        else:
            critical = self.is_critical_hit()
            summary["critical"] = critical
            # Apply damage
            damage = self.compute_damage(caster, target, critical)
            summary["effect"] = damage
            summary["sustained"] = target.take_damage(damage)
        return summary

class ReboundAttackEffect(AttackEffect):
    def __init__(self, element, power, accuracy, critical_hit_prob, rebound):
        # Call the parent Effect constructor first
        super(ReboundAttackEffect, self).__init__(element, power, accuracy, critical_hit_prob)

        # Store move accuracy and critical hit probability
        self.rebound = rebound

    # Override parent apply effect method for our AttackEffect
    def apply_effect(self, caster, target):
        summary = {
            "type"               : "rebound",
            "super_effective"    : self.element.is_strong_against(target.element),
            "not_very_effective" : self.element.is_weak_against(target.element),
            "target" : target,
            "evades" : False
        }
        # Test for evasion and report if target dodged
        if self.target_evades(caster, target):
            summary["evades"] = True
            summary["sustained"] = 0
            print("{} evades the attack.".format(target.name))
        else:
            critical = self.is_critical_hit()
            summary["critical"] = critical
            # Apply damage
            damage = self.compute_damage(caster, target, critical)
            summary["sustained"]=target.take_damage(damage)
            summary["effect"] = damage
            print("{} is hit by the rebound".format(caster.name))
            if summary["sustained"] > 0:
                rebound = (self.compute_damage(caster, caster)*self.rebound)//100
                rebound = max(1, rebound)
            else:
                rebound = 0
            caster.take_damage(rebound)
            summary["rebound"] = rebound

        return summary

class LeechAttackEffect(AttackEffect):
    def __init__(self, element, power, accuracy, critical_hit_prob, leech):
        # Call the parent Effect constructor first
        super(LeechAttackEffect, self).__init__(element, power, accuracy, critical_hit_prob)

        # Leech amount
        self.leech = leech

    # Override parent apply effect method for our LeechAttackEffect
    def apply_effect(self, caster, target):
        summary = {
            "type"               : "leech",
            "super_effective"    : self.element.is_strong_against(target.element),
            "not_very_effective" : self.element.is_weak_against(target.element),
            "target" : target,
            "evades" : False
        }
        # Test for evasion and report if target dodged
        if self.target_evades(caster, target):
            summary["evades"] = True
            summary["sustained"] = 0
            print("{} evades the attack.".format(target.name))
        else:
            critical = self.is_critical_hit()
            summary["critical"] = critical
            # Apply damage
            damage = self.compute_damage(caster, target, critical)
            summary["sustained"]=target.take_damage(damage)
            summary["effect"] = damage
            print("{} absorbs energy from {}".format(caster.name, target.name))
            if summary["sustained"] > 0:
                leeched = max(1, (summary["sustained"]*self.leech)//100)
                caster.restore_health(leeched)
                summary["leech"] = leeched
        return summary

class BoostStatEffect(Effect):
    def __init__(self, element, power, stat):
        super(BoostStatEffect, self).__init__(element, power)
        self.stat = stat

    def apply_effect(self, caster, target):
        summary = {
            "type"   : "stat_boost",
            "stat"   : self.stat,
            "target" : target,
            "power" : self.power
        }
        summary['effect'] = target.boost_stat(self.stat, self.power)
        return summary

class ReduceStatEffect(Effect):
    def __init__(self, element, power, accuracy, stat):
        super(ReduceStatEffect, self).__init__(element, power, accuracy)
        self.stat = stat

    def apply_effect(self, caster, target):
        summary = {
            "type"   : "stat_reduce",
            "stat"   : self.stat,
            "target" : target,
            "power"  : self.power
        }
        summary['effect'] = target.reduce_stat(self.stat, self.power)
        return summary

class HealingEffect(Effect):
    def apply_effect(self, caster, target):
        summary = {
            "type"   : "healing",
            "target" : target,
            "effect" : self.power
        }
        target.restore_health(self.power)
        return summary

##########################################
#                 Spells                 #
##########################################

class Spell(object):
    def __init__(self, name, effects, element):
        self.name    = name
        self.effects = effects
        self.element = element

    def is_castable_by(self, caster):
        return self.element.is_compatible_with(caster.element)

    def cast(self, caster, target):
        if isinstance(target, list):
            target = target[random.randint(0,len(target)-1)]

        summary = {
            "caster" : caster,
            "result" : []
        }
        for effect in self.effects:
            summary["result"].append(effect.apply_effect(caster, target))
        return summary

class GroupSpell(Spell):
    def cast(self, caster, targets):
        summary = {
            "caster" : caster,
            "result" : []
        }
        for target in targets:
            for effect in self.effects:
                summary["result"].append(effect.apply_effect(caster, target))
        return summary
##########################################
#                Commands                #
##########################################
class SpellCommand:
    def __init__(self, spell, caster, target):
        self.spell = spell
        self.caster = caster
        self.target = target

    def execute(self):
        raise NotImplementedError

class CastSpell(SpellCommand):
    def execute(self):
        if not self.spell.is_castable_by(self.caster):
            print("{} can't cast {}".format(self.caster.name, self.spell.name) )
            return { "caster": self.caster, "success" : False, "reason" : "cannot cast", "spell" : self.spell}
        else:
            print("{} casts {}".format(self.caster.name, self.spell.name) )
            result = self.spell.cast(self.caster, self.target)
            result['spell'] = self.spell
            result["success"] = True
            return result

##########################################
#                 Invoker                #
##########################################
class Magic:
    def __init__(self):
        return

    def execute(self, command):
        return command.execute()

##########################################
#                 Client                 #
##########################################
class SpellBook:
    spells   = {}
    elements = {}

    spell_constructors  = {
        'group'  : GroupSpell,
        'single' : Spell
    }

    effect_constructors = {
        'attack'        : AttackEffect,
        'rebound_attack' : ReboundAttackEffect,
        'leech_attack'   : LeechAttackEffect,
        'stat_boost'    : BoostStatEffect,
        'stat_reduce'   : ReduceStatEffect,
        'heal'          : HealingEffect
    }

    def __init__(self):
        self.magic = Magic()

    def cast_spell(self, spell, caster, target):
        spell = SpellBook.get_spell_object(spell)
        if spell != None:
            return self.magic.execute(CastSpell(spell, caster, target))
        else:
            return { "success" : False }

    @staticmethod
    def __load_elements(xml_tree):
        elements = xml_tree.find('elements').findall('element')

        # Load element types from the XML file
        for element in elements:
            # Get the name of the element
            name = element.attrib['name']

            # Get strengths, weaknesses and compatabilities
            strong = [elem.text for elem in element.findall('strong/element')]
            weak = [elem.text for elem in element.findall('weak/element')]
            compatible = [elem.text for elem in element.findall('compatible/element')]

            # Element has to be part of its own compatibility list
            compatible.append(name)

            # Add the element to our spell book
            SpellBook.elements[name] = Element(name, strong, weak, compatible)

    @staticmethod
    def __load_spells(xml_tree):
        spells   = xml_tree.find('spells').findall('spell')

        # Load spells into our spell book
        for spell in spells:
            # Get the name of the spell
            name    = spell.attrib['name']

            # Determine the spell's element type (with error checking)
            element = spell.find('element')

            # Element tag is missing
            if element == None:
                print("{} does not have element. Skipping".format(name))
                continue

            element = element.text

            # Element tag contained invalid text
            if element not in SpellBook.elements:
                print("{} has invalid element {}. Skipping".format(name, element))
                continue

            # Get the element from the list of elements loaded
            element = SpellBook.elements[element]

            # Load the effects that the spell has
            effects = []
            for effect in spell.findall('effect'):
                # Get the effect's type and remove that entry from the dictionary
                effect_type = effect.attrib.pop('type', None)

                # Cast dictionary elements to ints where possible
                for key in effect.attrib:
                    try:
                        new_val = int(effect.attrib[key])
                        effect.attrib[key] = new_val
                    except ValueError:
                        pass

                # Create the effect and append it to our list
                effects.append(SpellBook.effect_constructors[effect_type](element, **effect.attrib))

            # Create the spell from all that we've loaded
            SpellBook.spells[name] = SpellBook.spell_constructors[spell.attrib['type']](name, effects, element)

    @staticmethod
    def load_spell_book(spell_book):
        data = ET.parse(spell_book)
        tree = data.getroot()

        SpellBook.__load_elements(tree)
        SpellBook.__load_spells(tree)

    @staticmethod
    def get_element_object(identifier):
        if identifier not in SpellBook.elements:
            print("{} is not a real element".format(identifier))
            return None
        else:
            return SpellBook.elements[identifier]

    @staticmethod
    def get_spell_object(identifier):
        if identifier not in SpellBook.spells:
            print("{} is not a real spell".format(identifier))
            return None
        else:
            return SpellBook.spells[identifier]
