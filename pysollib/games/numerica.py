## vim:ts=4:et:nowrap
##
##---------------------------------------------------------------------------##
##
## PySol -- a Python Solitaire game
##
## Copyright (C) 2000 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1999 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1998 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1998 Galen Brooks <galen@nine.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING.
## If not, write to the Free Software Foundation, Inc.,
## 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
## Markus F.X.J. Oberhumer
## <markus@oberhumer.com>
## http://www.oberhumer.com/pysol
##
##---------------------------------------------------------------------------##

__all__ = []

# imports
import sys

# PySol imports
from pysollib.gamedb import registerGame, GameInfo, GI
from pysollib.util import *
from pysollib.stack import *
from pysollib.game import Game
from pysollib.layout import Layout
from pysollib.hint import AbstractHint, DefaultHint, CautiousDefaultHint
from pysollib.pysoltk import MfxCanvasText
from pysollib.mfxutil import kwdefault


# /***********************************************************************
# //
# ************************************************************************/

class Numerica_Hint(DefaultHint):
    # FIXME: demo is clueless

    #def _getDropCardScore(self, score, color, r, t, ncards):
        #FIXME: implement this method

    def _getMoveWasteScore(self, score, color, r, t, pile, rpile):
        assert r in (self.game.s.waste, self.game.s.talon) and len(pile) == 1
        score = 30000
        if len(t.cards) == 0:
            score = score - (KING - r.cards[0].rank) * 1000
        elif t.cards[-1].rank < r.cards[0].rank:
            # FIXME: add intelligence here
            score = 10000 + t.cards[-1].rank - len(t.cards)
        elif t.cards[-1].rank == r.cards[0].rank:
            score = 20000
        else:
            score = score - (t.cards[-1].rank - r.cards[0].rank) * 1000
        return score, color


# /***********************************************************************
# //
# ************************************************************************/

class Numerica_RowStack(BasicRowStack):
    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return 0
        # this stack accepts any one card from the Waste pile
        return from_stack is self.game.s.waste and len(cards) == 1

    def getBottomImage(self):
        return self.game.app.images.getReserveBottom()

    def getHelp(self):
        ##return _('Tableau. Accepts any one card from the Waste.')
        return _('Tableau. Build regardless of rank and suit.')


# /***********************************************************************
# // Numerica
# ************************************************************************/

class Numerica(Game):
    Hint_Class = Numerica_Hint
    Foundation_Class = StackWrapper(RK_FoundationStack, suit=ANY_SUIT)
    RowStack_Class = StackWrapper(Numerica_RowStack, max_accept=1)

    #
    # game layout
    #

    def createGame(self, rows=4):
        # create layout
        l, s = Layout(self), self.s
        decks = self.gameinfo.decks
        foundations = 4*decks

        # set window
        # (piles up to 20 cards are playable in default window size)
        h = max(2*l.YS, 20*l.YOFFSET)
        max_rows = max(rows, foundations)
        self.setSize(l.XM+(1.5+max_rows)*l.XS+l.XM, l.YM + l.YS + h)

        # create stacks
        x0 = l.XM + l.XS * 3 / 2
        if decks == 1:
            x = x0 + (rows-4)*l.XS/2
        else:
            x = x0
        y = l.YM
        for i in range(foundations):
            s.foundations.append(self.Foundation_Class(x, y, self, suit=i))
            x = x + l.XS
        x, y = x0, l.YM + l.YS
        for i in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self))
            x = x + l.XS
        self.setRegion(s.rows, (x0-l.XS/2, y-l.CH/2, 999999, 999999))
        x = l.XM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, 'n')
        y = y + l.YS
        s.waste = WasteStack(x, y, self, max_cards=1)

        # define stack-groups
        self.sg.openstacks = s.foundations + s.rows
        self.sg.talonstacks = [s.talon] + [s.waste]
        self.sg.dropstacks = s.rows + [s.waste]

    #
    # game overrides
    #

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealCards()          # deal first card to WasteStack

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))

    def getHighlightPilesStacks(self):
        return ()


class Numerica2Decks(Numerica):
    def createGame(self):
        Numerica.createGame(self, rows=6)


# /***********************************************************************
# // Lady Betty
# ************************************************************************/

class LadyBetty(Numerica):
    Foundation_Class = SS_FoundationStack

    def createGame(self):
        Numerica.createGame(self, rows=6)


# /***********************************************************************
# // Puss in the Corner
# ************************************************************************/

class PussInTheCorner_Talon(OpenTalonStack):
    rightclickHandler = OpenStack.rightclickHandler

    def canDealCards(self):
        if self.round != self.max_rounds:
            return True
        return False

    def clickHandler(self, event):
        if self.cards:
            return OpenStack.clickHandler(self, event)
        else:
            return TalonStack.clickHandler(self, event)

    def dealCards(self, sound=0):
        ncards = 0
        old_state = self.game.enterState(self.game.S_DEAL)
        if not self.cards and self.round != self.max_rounds:
            self.game.nextRoundMove(self)
            self.game.startDealSample()
            for r in self.game.s.rows:
                while r.cards:
                    self.game.moveMove(1, r, self, frames=4)
                    self.game.flipMove(self)
                    ncards += 1
            self.fillStack()
            self.game.stopSamples()
        self.game.leaveState(old_state)
        return ncards


class PussInTheCorner_Foundation(SS_FoundationStack):
    def __init__(self, x, y, game, **cap):
        kwdefault(cap, base_suit=ANY_SUIT)
        apply(SS_FoundationStack.__init__, (self, x, y, game, ANY_SUIT), cap)
    def acceptsCards(self, from_stack, cards):
        if not SS_FoundationStack.acceptsCards(self, from_stack, cards):
            return False
        if self.cards:
            # check the color
            if cards[0].color != self.cards[-1].color:
                return False
        return True
    def getHelp(self):
        return _('Foundation. Build up by color.')


class PussInTheCorner_RowStack(BasicRowStack):
    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return 0
        # this stack accepts any one card from the Talon
        return from_stack is self.game.s.talon and len(cards) == 1
    def getBottomImage(self):
        return self.game.app.images.getReserveBottom()
    def getHelp(self):
        ##return _('Tableau. Accepts any one card from the Waste.')
        return _('Tableau. Build regardless of rank and suit.')


class PussInTheCorner(Numerica):

    def createGame(self, rows=4):
        l, s = Layout(self), self.s
        self.setSize(l.XM+4*l.XS, l.YM+4*l.YS)
        for x, y in ((l.XM,        l.YM       ),
                     (l.XM+3*l.XS, l.YM       ),
                     (l.XM,        l.YM+3*l.YS),
                     (l.XM+3*l.XS, l.YM+3*l.YS),
                     ):
            stack = PussInTheCorner_RowStack(x, y, self,
                                             max_accept=1, max_move=1)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, 0
            s.rows.append(stack)
        for x, y in ((l.XM+  l.XS, l.YM+  l.YS),
                     (l.XM+  l.XS, l.YM+2*l.YS),
                     (l.XM+2*l.XS, l.YM+  l.YS),
                     (l.XM+2*l.XS, l.YM+2*l.YS),
                     ):
            s.foundations.append(PussInTheCorner_Foundation(x, y, self,
                                                            max_move=0))
        x, y = l.XM+3*l.XS/2, l.YM
        s.waste = s.talon = PussInTheCorner_Talon(x, y, self, max_rounds=2)
        l.createText(s.talon, 'se')

        # define stack-groups
        l.defaultStackGroups()


    def _shuffleHook(self, cards):
        return self._shuffleHookMoveToTop(cards,
                    lambda c: (c.rank == ACE, c.suit))


    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        self.s.talon.fillStack()


    def _autoDeal(self, sound=1):
        return 0


# /***********************************************************************
# // Frog
# // Fly
# ************************************************************************/

class Frog(Game):

    Hint_Class = Numerica_Hint
    ##Foundation_Class = SS_FoundationStack
    Foundation_Class = RK_FoundationStack

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 8*l.XS, l.YM + 2*l.YS+16*l.YOFFSET)

        # create stacks
        x, y, = l.XM, l.YM
        for i in range(8):
            if self.Foundation_Class is RK_FoundationStack:
                suit = ANY_SUIT
            else:
                suit = int(i/2)
            s.foundations.append(self.Foundation_Class(x, y, self,
                                 suit=suit, max_move=0))
            x += l.XS
        x, y = l.XM, l.YM+l.YS
        stack = OpenStack(x, y, self, max_accept=0)
        stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, l.YOFFSET
        s.reserves.append(stack)
        x += l.XS
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, "ss")
        x += l.XS
        s.waste = WasteStack(x, y, self, max_cards=1)
        x += l.XS
        for i in range(5):
            stack = Numerica_RowStack(x, y, self, max_accept=UNLIMITED_ACCEPTS)
            #stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, l.YOFFSET
            s.rows.append(stack)
            x = x + l.XS

        # define stack-groups
        l.defaultStackGroups()


    def startGame(self):
        self.startDealSample()
        n = 0
        f = 0
        while True:
            c = self.s.talon.cards[-1]
            if c.rank == ACE:
                r = self.s.foundations[f]
                f += 1
                ##r = self.s.foundations[c.suit*2]
            else:
                r = self.s.reserves[0]
                n += 1
            self.s.talon.dealRow(rows=[r])
            if n == 13:
                break
        self.s.talon.dealCards()


class Fly(Frog):

    Foundation_Class = RK_FoundationStack

    def _shuffleHook(self, cards):
        return self._shuffleHookMoveToTop(cards,
                    lambda c: (c.rank == ACE, c.suit))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        for i in range(13):
            self.s.talon.dealRow(self.s.reserves)
        self.s.talon.dealCards()


# /***********************************************************************
# // Gnat
# ************************************************************************/

class Gnat(Game):

    Hint_Class = Numerica_Hint

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        self.setSize(l.XM + 8*l.XS, l.YM + 2*l.YS+16*l.YOFFSET)

        # create stacks
        x, y = l.XM, l.YM
        s.talon = WasteTalonStack(x, y, self, max_rounds=1)
        l.createText(s.talon, "ss")
        x += l.XS
        s.waste = WasteStack(x, y, self, max_cards=1)
        x += l.XS
        for i in range(4):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            x += l.XS

        x, y = l.XM+2*l.XS, l.YM+l.YS
        for i in range(4):
            s.rows.append(Numerica_RowStack(x, y, self, max_accept=UNLIMITED_ACCEPTS))
            x += l.XS
        x = l.XM+6*l.XS
        for i in range(2):
            y = l.YM + l.YS/2
            for j in range(3):
                s.reserves.append(OpenStack(x, y, self, max_accept=0))
                y += l.YS
            x += l.YS

        # define stack-groups
        l.defaultStackGroups()


    def _shuffleHook(self, cards):
        return self._shuffleHookMoveToTop(cards,
                    lambda c: (c.rank == ACE, c.suit))

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.foundations)
        self.s.talon.dealRow(rows=self.s.reserves)
        self.s.talon.dealCards()


# /***********************************************************************
# // Gloaming
# // Chamberlain
# ************************************************************************/

class Gloaming_RowStack(Numerica_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return 0
        # this stack accepts any one card from reserves
        return from_stack in self.game.s.reserves


class Gloaming(Game):

    Hint_Class = Numerica_Hint
    Foundation_Class = SS_FoundationStack

    def createGame(self, reserves=3, rows=5):
        # create layout
        l, s = Layout(self), self.s

        # set window
        n = 52/reserves+1
        w, h = l.XM + (reserves+rows+1)*l.XS, l.YM + 2*l.YS+n*l.YOFFSET
        self.setSize(w, h)

        # create stacks
        x, y = l.XM+(reserves+rows+1-4)*l.XS/2, l.YM
        for i in range(4):
            if self.Foundation_Class is RK_FoundationStack:
                suit = ANY_SUIT
            else:
                suit = i
            s.foundations.append(self.Foundation_Class(x, y, self,
                                 suit=suit, max_move=0))
            x += l.XS

        x, y = l.XM, l.YM+l.YS
        for i in range(reserves):
            stack = OpenStack(x, y, self, max_accept=0)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 0, l.YOFFSET
            s.reserves.append(stack)
            x += l.XS

        x += l.XS
        for i in range(rows):
            s.rows.append(Gloaming_RowStack(x, y, self, max_accept=UNLIMITED_ACCEPTS))
            x += l.XS

        s.talon = InitialDealTalonStack(w-l.XS, h-l.YS, self)

        # default
        l.defaultAll()


    def startGame(self):
        n = 52/len(self.s.reserves)+1
        for i in range(n-3):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.reserves)
        self.s.talon.dealRow(rows=self.s.reserves)
        self.s.talon.dealRowAvail(rows=self.s.reserves)


class Chamberlain(Gloaming):
    Foundation_Class = RK_FoundationStack
    def createGame(self, reserves=3, rows=5):
        Gloaming.createGame(self, reserves=4, rows=3)


# /***********************************************************************
# // Toad
# ************************************************************************/

class Toad_TalonStack(DealRowTalonStack):
    def canDealCards(self):
        if not DealRowTalonStack.canDealCards(self):
            return False
        for r in self.game.s.reserves:
            if r.cards:
                return False
        return True
    def dealCards(self, sound=0):
        self.dealRow(rows=self.game.s.reserves, sound=sound)


class Toad(Game):
    #Hint_Class = Numerica_Hint

    def createGame(self, reserves=3, rows=5):
        # create layout
        l, s = Layout(self), self.s

        # set window
        w, h = l.XM+11*l.XS, l.YM+6*l.YS
        self.setSize(w, h)

        # create stacks
        x, y = w-l.XS, h-l.YS
        s.talon = Toad_TalonStack(x, y, self)
        l.createText(s.talon, "n")
        x, y = l.XM, l.YM
        for i in range(8):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i/2))
            x += l.XS
        x, y = l.XM+3*l.XS/2, l.YM+l.YS
        for i in range(5):
            s.rows.append(Gloaming_RowStack(x, y, self, max_accept=UNLIMITED_ACCEPTS))
            x += l.XS
        y = l.YM+l.YS/2
        for i in (3, 3, 3, 3, 1):
            x = l.XM+8*l.XS
            for j in range(i):
                s.reserves.append(OpenStack(x, y, self, max_accept=0))
                x += l.XS
            y += l.YS

        # define stack-groups
        l.defaultStackGroups()

    def startGame(self):
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.reserves)


# /***********************************************************************
# // Shifting
# ************************************************************************/

class Shifting_RowStack(Numerica_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return False
        if from_stack is self.game.s.waste:
            return True
        if not self.cards:
            return cards[0].rank == KING
        if (from_stack in self.game.s.rows and
            self.cards[-1].rank-cards[0].rank == 1):
            return True
        return False


class Shifting(Numerica):
    RowStack_Class = StackWrapper(Shifting_RowStack, max_accept=1)


# /***********************************************************************
# // Strategerie
# ************************************************************************/

class Strategerie_Talon(OpenTalonStack):
    rightclickHandler = OpenStack.rightclickHandler


class Strategerie_RowStack(BasicRowStack):

    def acceptsCards(self, from_stack, cards):
        if not BasicRowStack.acceptsCards(self, from_stack, cards):
            return False
        if from_stack is self.game.s.talon or from_stack in self.game.s.reserves:
            return True
        return False

    def getBottomImage(self):
        return self.game.app.images.getReserveBottom()

    def getHelp(self):
        return _('Tableau. Build regardless of rank and suit.')


class Strategerie_ReserveStack(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        if not ReserveStack.acceptsCards(self, from_stack, cards):
            return False
        if from_stack is self.game.s.talon:
            return True
        return False


class Strategerie(Game):
    Hint_Class = Numerica_Hint

    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        l.freeCellLayout(rows=4, reserves=4, texts=1)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = Strategerie_Talon(l.s.talon.x, l.s.talon.y, self)
        for r in l.s.foundations:
            s.foundations.append(RK_FoundationStack(r.x, r.y, self))
        for r in l.s.rows:
            s.rows.append(Strategerie_RowStack(r.x, r.y, self,
                                               max_accept=UNLIMITED_ACCEPTS))
        for r in l.s.reserves:
            s.reserves.append(Strategerie_ReserveStack(r.x, r.y, self))
        # default
        l.defaultAll()
        self.sg.dropstacks.append(s.talon)

    def startGame(self):
        self.startDealSample()
        self.s.talon.fillStack()



# register the game
registerGame(GameInfo(257, Numerica, "Numerica",
                      GI.GT_NUMERICA | GI.GT_CONTRIB, 1, 0, GI.SL_BALANCED,
                      altnames="Sir Tommy"))
registerGame(GameInfo(171, LadyBetty, "Lady Betty",
                      GI.GT_NUMERICA, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(355, Frog, "Frog",
                      GI.GT_NUMERICA, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(356, Fly, "Fly",
                      GI.GT_NUMERICA, 2, 0, GI.SL_BALANCED,
                      rules_filename='frog.html'))
registerGame(GameInfo(357, Gnat, "Gnat",
                      GI.GT_NUMERICA, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(378, Gloaming, "Gloaming",
                      GI.GT_NUMERICA | GI.GT_OPEN | GI.GT_ORIGINAL, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(379, Chamberlain, "Chamberlain",
                      GI.GT_NUMERICA | GI.GT_OPEN | GI.GT_ORIGINAL, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(402, Toad, "Toad",
                      GI.GT_NUMERICA | GI.GT_ORIGINAL, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(430, PussInTheCorner, "Puss in the Corner",
                      GI.GT_NUMERICA, 1, 1, GI.SL_BALANCED))
registerGame(GameInfo(435, Shifting, "Shifting",
                      GI.GT_NUMERICA, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(472, Strategerie, "Strategerie",
                      GI.GT_NUMERICA, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(558, Numerica2Decks, "Numerica (2 decks)",
                      GI.GT_NUMERICA, 2, 0, GI.SL_BALANCED))


