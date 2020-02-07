# -*- coding: utf-8 -*-
"""
This file is part of ac-maps.
    ac-maps is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    ac-maps is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with ac-maps.  If not, see <http://www.gnu.org/licenses/>.
"""



import numpy as np
from scipy.sparse.csgraph import minimum_spanning_tree

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt



class acm:
    ''' This class implements an Auto Contractive Map.
    '''

    def __init__(self, _inputLength, _contraction):
        ''' Initialization function.

            Arguments:
                _inputLength (int): Length of input vector
                _contraction (float): Contraction parameter, _contraction>1.
        '''

        # Length of input vector
        self.N = _inputLength

        # Contraction parameter
        self.C = _contraction
 
        # First layer
        self.v = np.full((1, self.N), 0.01, dtype=float)[0]
 
        # Hidden layer
        self.w = np.full((self.N, self.N), 0.01, dtype=float)
        
        # Neuron values
        self.mHidden = np.zeros((1, self.N), dtype=float)[0]
        self.mOut = np.zeros((1, self.N), dtype=float)[0]

        # Training data
        self.training = np.zeros((1, self.N), dtype=float)

        # Labels of training data
        self.label = ['' for x in range(self.N)]

        # Throw exception, if computation fails
        np.seterr('raise')



    def runOnce(self, _mIn):
        ''' This function performs one run of training using _mIn as input vector.

            Arguments:
                _mIn (np.array(dtype=float)): Input vector.
        '''

        # 0. Normalize input to be [0, 1]
        mIn = np.interp(_mIn, (_mIn.min(), _mIn.max()), (0, 1))
        assert np.amin(mIn) >= 0, 'Training sample holds data <0: ' + str(mIn)
        assert np.amax(mIn) <= 1, 'Training sample holds data >1: ' + str(mIn)

        # 1. Signal In to Hidden
        for i in range(self.N):
            self.mHidden[i] = mIn[i] * (1 - self.v[i]/self.C)

        # 2. Adapt weights In to Hidden (v)
        # The formula is actualle m_s * (1 - (v/C)^2)
        for i in range(self.N):
            self.v[i] += (mIn[i] - self.mHidden[i]) * (1 - (self.v[i]/self.C))

        # 3. Signal Hidden to Out
        self.net = np.zeros((1, self.N), dtype=float)[0]
        for i in range(self.N):
            for j in range(self.N):
                self.net[i] += self.mHidden[j] * (1 - (self.w[i][j]/self.C))

        for i in range(self.N):
            self.mOut[i] = self.mHidden[i] * (1 - self.net[i]/self.C)

        # 4. Adapt weights Hidden to Out (w)
        for i in range(self.N):
            for j in range(self.N):
                # Perform computation in single steps to avoid overflow
                self.w[i][j] += (self.mHidden[i] - self.mOut[i]) * (1 - self.w[i][j]/self.C) * self.mHidden[j]



    def createTrainingRandom(self):
        ''' This function creates 1000 training samples.

            The each vector is drawn randomly from a uniform distribution, meaning there is no correlation.
        '''
        self.training = np.random.rand(1000, self.N)

        # Create labels
        self.label = []
        for j in range(self.N):
            self.label.append('R' + str(j))


    def createTrainingCorrelated(self):
        ''' This function creates 1000 training samples.

            The each vector is made up as follows:
            [rand1, 2*rand1, 3*rand1, rand1^2, 2*rand1^2, 3*rand1^2, rand2, rand3, rand4, ... randN]
        '''

        if self.N < 6:
            raise ValueError('For createTrainingCorrelated an input vector size of at least 6 is needed.')

        # Create labels
        self.label= ['R1', '2xR1', 'R1+0.1', 'R1^2', '2*R1^2', '3xR1^2', 'R2>0.9', 'R3>0.9', 'R4>0.9', 'R5>0.9'] 
        for i in range(8, self.N):
            self.label.append('R' + str(i))


        self.training = []
        for i in range(1000):
            v = np.zeros(self.N, dtype=float)
            v[0] = np.random.rand(1)[0]
            v[1] = v[0]*2
            v[2] = v[0]+0.1
            v[3] = v[0]*v[0]
            v[4] = v[0]*v[0]*2
            v[5] = v[0]*v[0]*3
            v[6] = np.random.rand(1)[0]*0.1 + 0.9
            v[7] = np.random.rand(1)[0]*0.1 + 0.9
            v[8] = np.random.rand(1)[0]*0.1 + 0.9
            v[9] = np.random.rand(1)[0]*0.1 + 0.9
            #for j in range(8, self.N):
            #    v[j] = np.random.rand(1)
            #    self.label.append('R' + str(j))

            self.training.append(v)




    def run(self):
        ''' This function trains the map given the training samples in self.training.
        '''

        self.cnt = 0
        for x in self.training:
            self.runOnce(x)
            self.cnt += 1


            # Check, if training is finished
            # Requested precision is 1e-6,
            # After that output oscillates and may throw RuntimeWarning:Overflow encounter
            sumOut = np.sum(self.mOut)
            if sumOut >= 0  and sumOut < 1e-6:
                break

        # Compute minimum spanning tree (mst)
        self.mst = minimum_spanning_tree(self.w)



    def printTree(self):
        ''' This function prints the results of self.run().
        '''

        print('Total number of runs: ' + str(self.cnt) + '\n')

        corr = self.mst.toarray().astype(float)
        for i in range(self.N):
            for j in range(self.N):
                if not corr[i][j] == 0:
                    print('Connection: ' + str(self.label[i]) + ' --> \t' + str(self.label[j]) + '\t' + str(corr[i][j]))



    def draw(self):
        ''' This function draws the tree, which results from training.
        '''
        corr = self.mst.toarray().astype(float)
        cellFrom = []
        cellTo = []
        corrEdge = []
        for i in range(self.N):
            for j in range(self.N):
                if not corr[i][j] == 0:
                    cellFrom.append(self.label[i])
                    cellTo.append(self.label[j])
                    corrEdge.append(corr[i][j])

        df = pd.DataFrame({'from':cellFrom, 'to':cellTo, 'weight': corrEdge})

        # Build your graph
        G=nx.from_pandas_edgelist(df, 'from', 'to', 'weight')

        # Plot the network:
        nx.draw(G, with_labels=True, node_color='orange', node_size=400, edge_color='black', linewidths=1, font_size=15)
        plt.show()




def main():
    ''' This program trains an Auto Contractive Map.
    '''

    # Length of input vector
    N = 10

    # Contraction parameter
    C = 2

    # Class initialization
    cAcm = acm(N, C)

    # Create training samples
    #cAcm.createTrainingRandom()
    cAcm.createTrainingCorrelated()

    # Run training
    cAcm.run()

    # Print results
    cAcm.printTree()

    # Draw resulting tree
    cAcm.draw()



if __name__ == "__main__":
    # execute only if run as a script
    main()
