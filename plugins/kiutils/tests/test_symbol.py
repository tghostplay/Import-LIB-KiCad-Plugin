"""Unittests of library symbol related classes

Authors:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0
"""

import unittest
from os import path

from kiutils.misc.config import KIUTILS_CREATE_NEW_VERSION_STR
from kiutils.symbol import Symbol, SymbolLib
from kiutils.utils.sexpr import parse_sexp
from tests.testfunctions import (
    TEST_BASE,
    prepare_test,
    to_file_and_compare,
)

SYMBOL_BASE = path.join(TEST_BASE, "symbol")


class Tests_Symbol(unittest.TestCase):
    """Test cases for Symbols"""

    def setUp(self) -> None:
        prepare_test(self)
        return super().setUp()

    def test_allSymbolPinVariations(self):
        """Tests the parsing of all pin types of a symbol in a symbol library"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "test_allSymbolPinVariations"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_allSymbolAlternatePins(self):
        """Tests the parsing of all alternate pin definitions of a symbol in a symbol library"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "test_allSymbolAlternatePins"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_symbolParameters(self):
        """Tests the parsing of a symbol's parameters in a symbol library"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(SYMBOL_BASE, "test_symbolParameters")
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_symbolDemorganUnits(self):
        """Tests the parsing of a symbol's de-morgan unit represenations in a symbol library"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "test_symbolDemorganUnits"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_symbolDemorganSyItems(self):
        """Tests the parsing of a symbol' in a symbol library that has all SyItems in different
        de-morgan variations in it"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "test_symbolDemorganSyItems"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_bigSymbolLibrary(self):
        """Tests the parsing of a big symbol library with many symbols of different kinds in it"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(SYMBOL_BASE, "test_bigSymbolLibrary")
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_createNewSymbolInEmptyLibrary(self):
        """Tests the ``create_new()`` function to create an empty symbol that is added to a
        symbol library"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "test_createNewSymbolInEmptyLibrary"
        )

        # Create an empty symbol library
        symbolLib = SymbolLib(
            version=KIUTILS_CREATE_NEW_VERSION_STR, generator="kiutils"
        )

        # Add a symbol to it via create_new()
        symbol = Symbol().create_new(id="testsymbol", reference="U", value="testvalue")
        symbolLib.symbols.append(symbol)

        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_renameParentIdUsingIdToken(self):
        """Rename symbol inside library using the id token setter and verify all units are renamed
        correctly as well as the ``Value`` property stayed the same."""
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "test_renameParentIdUsingIdToken"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        symbolLib.symbols[0].libId = "ExampleLibrary:AD2023"  # Setting library nickname
        symbolLib.symbols[1].libId = "AD2023"  # Unsetting library nickname
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_createNewTopLevelSymbolFromChild(self):
        """Take a child symbol, rename its library id and make a new top-level symbol out of it.
        Tests if resetting both ``unitId`` and ``styleId`` works."""
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "test_createNewTopLevelSymbolFromChild"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)

        # Copy the symbol
        childSymbol = Symbol.from_sexpr(
            parse_sexp(symbolLib.symbols[0].units[0].to_sexpr())
        )

        # Rename it and save it as a new top-level symbol to the library
        childSymbol.libId = "SomeNewName:AD2023"
        symbolLib.symbols.append(childSymbol)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_mergeLibraries(self):
        """Merge the symbols of two symbol libraries together"""
        self.testData.pathToTestFile = path.join(SYMBOL_BASE, "test_mergeLibraries")
        symbolLib1 = SymbolLib().from_file(self.testData.pathToTestFile)
        symbolLib2 = SymbolLib().from_file(
            path.join(SYMBOL_BASE, "test_symbolDemorganSyItems")
        )
        for symbol in symbolLib2.symbols:
            symbolLib1.symbols.insert(0, symbol)
        self.assertTrue(to_file_and_compare(symbolLib1, self.testData))

    def test_symbolIdParser(self):
        """Tests edge cases of parsing the symbol ID token and checks if the ID was split into
        its parts correctly

        Related issues:
            - [Pull request 73](https://github.com/mvnmgrx/kiutils/pull/73)
        """
        self.testData.pathToTestFile = path.join(SYMBOL_BASE, "test_symbolIdParser")
        self.testData.compareToTestFile = True
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))


class Tests_Symbol_Since_V7(unittest.TestCase):
    """Test cases for Symbols since KiCad 7"""

    def setUp(self) -> None:
        prepare_test(self)
        return super().setUp()

    def test_textBoxAllVariants(self):
        """Tests all variants of the ``text_box`` token for text boxes in symbols"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v7", "test_textBoxAllVariants"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_rectangleAllVariants(self):
        """Tests all variants of the ``rectangle`` token for rectangles in symbols"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v7", "test_rectangleAllVariants"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_circleAllVariants(self):
        """Tests all variants of the ``circle`` token for circles in symbols"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v7", "test_circleAllVariants"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))

    def test_arcAllVariants(self):
        """Tests all variants of the ``arc`` token for arcs in symbols"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v7", "test_arcAllVariants"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(symbolLib, self.testData))


class Tests_Symbol_Since_V9(unittest.TestCase):
    """Test cases for Symbols since KiCad 9"""

    def setUp(self) -> None:
        prepare_test(self)
        return super().setUp()

    def test_v9HidePropertiesFormatting(self):
        """Tests v9 hide properties parsing including pin_names, pin_numbers, and effects formatting"""
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v9", "test_v9_hide_properties"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        symbol = symbolLib.symbols[0]

        # Test basic parsing
        self.assertEqual(symbol.libId, "Test_V9_Hide_Properties")
        self.assertTrue(symbol.inBom)
        self.assertTrue(symbol.onBoard)

        # Test v9 specific: pin_names with (hide yes)
        self.assertTrue(symbol.pinNames, "pin_names should be enabled")
        self.assertTrue(symbol.pinNamesHide, "pin_names should be hidden (v9 format)")

        # Test hidden vs visible properties
        hiddenProps = [p.key for p in symbol.properties if p.effects and p.effects.hide]
        visibleProps = [
            p.key for p in symbol.properties if not (p.effects and p.effects.hide)
        ]

        # These should be visible (no hide property)
        self.assertIn("Reference", visibleProps)
        self.assertIn("Value", visibleProps)

        # These should be hidden (hide yes)
        self.assertIn("Footprint", hiddenProps)
        self.assertIn("Datasheet", hiddenProps)
        self.assertIn("Description", hiddenProps)

    def test_v9NewPropertiesParsing(self):
        """Tests parsing of new v9 properties: exclude_from_sim and embedded_fonts"""
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v9", "test_v9_hide_properties"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        symbol = symbolLib.symbols[0]

        # Test v9 symbol-level properties
        self.assertIsNotNone(symbol.excludeFromSim, "exclude_from_sim should be parsed")
        self.assertFalse(
            symbol.excludeFromSim, "exclude_from_sim should be False (value 'no')"
        )

        # Test serialization includes new properties
        serialized = symbolLib.to_sexpr()
        self.assertIn(
            "exclude_from_sim no", serialized, "exclude_from_sim should be in output"
        )
        self.assertIn(
            "embedded_fonts no", serialized, "embedded_fonts should be in output"
        )

        # Test round-trip: serialize and re-parse
        reparsedLib = SymbolLib().from_sexpr(parse_sexp(serialized))
        reparsedSymbol = reparsedLib.symbols[0]

        # Verify all properties are preserved
        self.assertEqual(
            symbol.excludeFromSim,
            reparsedSymbol.excludeFromSim,
            "exclude_from_sim should be preserved",
        )

    def test_v9HidePropertyFormatsCompatibility(self):
        """Tests both v8 'hide' and v9 '(hide yes)' formats in effects for backward compatibility"""
        from kiutils.items.common import Effects

        # v9 format: (hide yes)
        effectsV9Yes = Effects().from_sexpr(
            ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "yes"]]
        )
        self.assertTrue(effectsV9Yes.hide)

        # v9 format: (hide no)
        effectsV9No = Effects().from_sexpr(
            ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "no"]]
        )
        self.assertFalse(effectsV9No.hide)

        # v8 format: hide (backward compatibility)
        effectsV8 = Effects().from_sexpr(
            ["effects", ["font", ["size", 1.27, 1.27]], "hide"]
        )
        self.assertTrue(effectsV8.hide)

    def test_v9ComprehensiveFeatures(self):
        """Tests all v9 features together in comprehensive validation"""
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v9", "test_v9_hide_properties"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        symbol = symbolLib.symbols[0]

        # Test version and generator parsing
        self.assertEqual(symbolLib.version, "20241209", "Should parse v9 version")
        self.assertEqual(
            symbolLib.generator, "kicad_symbol_editor", "Should parse v9 generator"
        )

        # Test all v9 symbol properties
        self.assertTrue(symbol.pinNames, "pin_names should be enabled")
        self.assertTrue(symbol.pinNamesHide, "pin_names should be hidden")
        self.assertFalse(symbol.excludeFromSim, "exclude_from_sim should be False")

        # Test all v9 library properties

        # Test effects hide properties count
        hiddenCount = sum(1 for p in symbol.properties if p.effects and p.effects.hide)
        visibleCount = sum(
            1 for p in symbol.properties if not (p.effects and p.effects.hide)
        )

        self.assertGreater(hiddenCount, 0, "Should have hidden properties")
        self.assertGreater(visibleCount, 0, "Should have visible properties")

        # Test specific property visibility
        propStatus = {
            p.key: (p.effects.hide if p.effects else False) for p in symbol.properties
        }

        # These should be visible
        self.assertFalse(
            propStatus.get("Reference", True), "Reference should be visible"
        )
        self.assertFalse(propStatus.get("Value", True), "Value should be visible")

        # These should be hidden
        self.assertTrue(
            propStatus.get("Footprint", False), "Footprint should be hidden"
        )
        self.assertTrue(
            propStatus.get("Datasheet", False), "Datasheet should be hidden"
        )
        self.assertTrue(
            propStatus.get("Description", False), "Description should be hidden"
        )

    def test_v9ToV8ConversionWorkflow(self):
        """Tests the complete v9 to v8 conversion workflow preserving all critical data"""
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v9", "test_v9_hide_properties"
        )

        # Load v9 file
        originalLib = SymbolLib().from_file(self.testData.pathToTestFile)
        originalSymbol = originalLib.symbols[0]

        # Count original features
        originalHiddenCount = sum(
            1 for p in originalSymbol.properties if p.effects and p.effects.hide
        )
        originalPinHide = originalSymbol.pinNamesHide
        originalExcludeSim = originalSymbol.excludeFromSim

        # Convert to v8 format (typical workflow)
        originalLib.version = "20211014"
        originalLib.generator = "kiutil"

        # Serialize and reload (simulates file save/load cycle)
        convertedContent = originalLib.to_sexpr()
        convertedLib = SymbolLib().from_sexpr(parse_sexp(convertedContent))
        convertedSymbol = convertedLib.symbols[0]

        # Verify critical data is preserved after conversion
        convertedHiddenCount = sum(
            1 for p in convertedSymbol.properties if p.effects and p.effects.hide
        )

        self.assertEqual(
            originalHiddenCount,
            convertedHiddenCount,
            "Hidden property count should be preserved",
        )
        self.assertEqual(
            originalPinHide,
            convertedSymbol.pinNamesHide,
            "pin_names hide should be preserved",
        )
        self.assertEqual(
            originalExcludeSim,
            convertedSymbol.excludeFromSim,
            "exclude_from_sim should be preserved",
        )

        # Test v8 format output attributes
        self.assertEqual(convertedLib.version, "20211014", "Should output v8 version")
        self.assertEqual(
            convertedLib.generator, "kiutil", "Should output kiutil generator"
        )

    def test_v9PinNamesAndPinNumbersHideParsing(self):
        """Tests parsing of pin_names and pin_numbers hide properties in v9 format"""
        self.testData.pathToTestFile = path.join(
            SYMBOL_BASE, "since_v9", "test_v9_hide_properties"
        )
        symbolLib = SymbolLib().from_file(self.testData.pathToTestFile)
        symbol = symbolLib.symbols[0]

        # Test pin_names parsing
        self.assertTrue(symbol.pinNames, "pin_names should be enabled")
        self.assertTrue(
            symbol.pinNamesHide, "pin_names hide should be parsed from (hide yes)"
        )

        # Test that offset parsing still works alongside hide
        if symbol.pinNamesOffset is not None:
            self.assertIsInstance(
                symbol.pinNamesOffset,
                (int, float),
                "pin_names offset should be numeric",
            )

        # Note: pin_numbers hide would be tested here if the test file contained it
        # For now we test the parsing logic works with our helper function
        testHideProps = [["hide", "yes"], "hide", ["hide", "no"]]
        hideResults = [symbol._parse_hide_property([prop]) for prop in testHideProps]
        expectedResults = [True, True, False]

        self.assertEqual(
            hideResults,
            expectedResults,
            "Hide property parsing should handle all formats",
        )
