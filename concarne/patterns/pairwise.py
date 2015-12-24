"""

Pairwise patterns. 

"""
__all__ = [
  "PairwiseTransformationPattern",
  "PairwisePredictTransformationPattern",
]

from .base import Pattern

import lasagne.objectives
import lasagne.layers

class PairwiseTransformationPattern(Pattern):
    """
    Base class for all pairwise transformation patterns. The general framework
    is as follows::
    
                   psi
      x_i ----> s_i ------> y
           phi      \\
                     \\
      x_j ----> s_j -->  ~c
           phi       beta

    Note that self.context_var should represent x_j, whereas self.input_var 
    represents self.x_i. The variable ``c'' in the picture is then represented
    by context_transform_var.
    
    The subclass of this pattern decides what beta looks like.
    

    Parameters
    ----------
    context_transform_var: a Theano variable representing the transformation.
    """
  
    @property
    def default_target_objective(self):
        return lasagne.objectives.categorical_crossentropy  
  
    @property  
    def default_context_objective(self):
        return lasagne.objectives.squared_error
  
    def __init__(self, context_transform_var=None, **kwargs):
        self.context_input_layer = None
        super(PairwiseTransformationPattern, self).__init__(**kwargs)
        
        self.context_transform_var = context_transform_var
        assert (self.context_transform_var is not None)

        self._create_target_objective()
        self._create_context_objective()                                     

    def _create_context_objective(self):
        if self.context_loss is None:
            assert (self.input_var is not None)
            assert (self.context_var is not None)
            
            if self.context_loss_fn is None:
                fn = self.default_context_objective
            else:
                #print ("Context loss is function object: %s" % str(self.context_loss_fn))
                fn = self.context_loss_fn
            
            self.context_loss = fn(
                self.get_beta_output_for(self.input_var, self.context_var), 
                self.context_transform_var
            ).mean()


    def get_beta_output_for(self, input_i, input_j, **kwargs):
        raise NotImplementedError()

    @property
    def training_input_vars(self):
        return (self.input_var, self.target_var, self.context_var, self.context_transform_var)
          
    @property
    def context_vars(self):
        return (self.context_var, self.context_transform_var)        

class PairwisePredictTransformationPattern(PairwiseTransformationPattern):
    """
    The :class:`PairwisePredictTransformationPattern` is a contextual pattern where 
    c is used as given information about the transformation between pairs
    of input pairs. The function beta is then used to predict c from a pair
    (x_i, x_j)::

                   psi
       x_i ----> s_i ------> y
            phi      \\
                      \\
       x_j ----> s_j ------> ~c
            phi       beta(s_i, s_j)

    Note that self.context_var should represent x_j, whereas self.input_var 
    represents self.x_i. The variable ``c'' in the picture is then represented
    by context_transform_var.
    

    Parameters
    ----------
    context_transform_var: a Theano variable representing the transformation.
    """
  
    def __init__(self, **kwargs):
        super(PairwisePredictTransformationPattern, self).__init__(**kwargs)

    @property  
    def default_beta_input(self):
        if self.context_input_layer is None:
            # create input layer
            #print ("Creating input layer for beta")
            context_dim = self.context_shape
            if isinstance(self.context_shape, int):
                context_dim = (None, self.context_shape)
            self.context_input_layer = lasagne.layers.InputLayer(shape=context_dim,
                                        input_var=self.context_var)
        return self.context_input_layer

    def get_beta_output_for(self, input_i, input_j, **kwargs):
        phi_i_output = self.phi.get_output_for(input_i, **kwargs)
        phi_j_output = self.phi.get_output_for(input_j, **kwargs)
        diff = phi_i_output-phi_j_output
        if self.beta is not None:
            return self.beta.get_output_for(diff, **kwargs)
        else:
            return diff