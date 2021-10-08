# -*- coding: utf-8 -*-
import numpy as np

from .. import solution


class InterfaceSolutionResult(solution.SolutionResult):
    def __init__(self, equilibrium_system, x, TK, 
                 x_bulk, transport_vector, reaction_imp, *args, **kwargs):
        super().__init__(equilibrium_system, x, TK, **kwargs)
        self._transport_fluxes = transport_vector*(x_bulk - x)
        self._interface_indexes = equilibrium_system._explicit_interface_indexes + \
                                  equilibrium_system._implicit_interface_indexes
        if reaction_imp is None:
            self._reaction_fluxes = self._make_reaction_fluxes_1(equilibrium_system)
        else:
            self._reaction_fluxes = self._make_reaction_fluxes_2(equilibrium_system, reaction_imp)
    
    def _make_reaction_fluxes_1(self, equilibrium_system):
        #First calculate J^R, whose order will be self._interface_indexes controled
        reaction_stoich_matrix = self.solid_stoich_matrix[self._interface_indexes, :]
        balance_matrix = self.formula_matrix[2:, :] #Reduced formula matrix
        reduced_balance_matrix = balance_matrix[:, 1:] #Only solutes
        b = reduced_balance_matrix@self._transport_fluxes
        A = balance_matrix@reaction_stoich_matrix.transpose()
        jr, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        reaction_fluxes = np.zeros(len(self.solid_phase_names))
        for i, phase in enumerate(equilibrium_system.interface_phases):
            reaction_fluxes[equilibrium_system.interface_indexes_dict[phase]] = jr[i]
        return reaction_fluxes

    def _make_reaction_fluxes_2(self, equilibrium_system, jr_imp):
        #First calculate J^R, whose order will be self._interface_indexes controled
        reaction_stoich_matrix_exp = \
            self.solid_stoich_matrix[equilibrium_system._explicit_interface_indexes, :]
        reaction_stoich_matrix_imp = \
            self.solid_stoich_matrix[equilibrium_system._implicit_interface_indexes, :]
        balance_matrix = self.formula_matrix[2:, :] #Reduced formula matrix
        reduced_balance_matrix = balance_matrix[:, 1:] #Only solutes
        b1 = reduced_balance_matrix@self._transport_fluxes
        b2 = -balance_matrix@reaction_stoich_matrix_imp.transpose()@jr_imp
        b = b1 + b2
        A = balance_matrix@reaction_stoich_matrix_exp.transpose()
        jr_exp, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        jr = np.hstack([jr_exp, jr_imp])
        reaction_fluxes = np.zeros(len(self.solid_phase_names))
        for i, phase in enumerate(equilibrium_system.interface_phases):
            reaction_fluxes[equilibrium_system.interface_indexes_dict[phase]] = jr[i]
        return reaction_fluxes

    @property
    def reaction_fluxes(self): #mol/m^2 s
        return {phase: self._reaction_fluxes[i] for i, phase in enumerate(self.solid_phase_names)}
                #Next make reaction fluxes including non-reacting species
        
    @property
    def transport_fluxes(self): #mol/m^2 s
        return {solute: self._transport_fluxes[i] for i, solute in enumerate(self.solutes)}