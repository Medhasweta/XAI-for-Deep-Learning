#%%

import numpy as np
from matplotlib import pyplot as plt
import tensorflow as tf
from math import ceil
from time import time
from sklearn import linear_model
from io import BytesIO
from PIL import Image
import os
from xplique.attributions import GradCAM, GradCAMPP, Occlusion, Rise, IntegratedGradients, Lime, KernelShap
from images import plot_attribution
import streamlit as st

os.chdir("/home/ubuntu/attempt2")

st.header("XAI Demos")

if "phase1" not in st.session_state:
    st.session_state["phase1"] = False

if "phase2" not in st.session_state:
    st.session_state["phase2"] = False

if "phase2.5" not in st.session_state:
    st.session_state["phase2.5"] = False

if "phase3" not in st.session_state:
    st.session_state["phase3"] = False

# Phase 1. Let user pick image:
image = st.file_uploader("Chosse an image:")

if image is None:
    st.stop()

image = image.read()
image = Image.open(BytesIO(image))
image.save("downloaded_image.jpg")

st.image(image)

st.session_state["phase1"] = True

if st.session_state["phase1"] == True:
    
    # Phase 2. Let user pick pretrained model
    
    option = st.selectbox(
    "Choose pretrained model:",
    ('Select model', 'InceptionV3', 'ResNet50'))

    if option == 'Select model':
        st.stop()
    
    if option == "InceptionV3":
        model = tf.keras.applications.InceptionV3()
        x = np.expand_dims(tf.keras.preprocessing.image.load_img(os.getcwd() + os.sep + "downloaded_image.jpg", target_size=(299, 299)), 0)
        x = np.array(x, dtype=np.float32) / 255.0

        y = np.expand_dims(tf.keras.utils.to_categorical(277, 1000), 0)
    
    if option == "ResNet50":
        model = tf.keras.applications.ResNet50()
        x = np.expand_dims(tf.keras.preprocessing.image.load_img(os.getcwd() + os.sep + "downloaded_image.jpg", target_size=(224, 224)), 0)
        x = np.array(x, dtype=np.float32) / 255.0

        y = np.expand_dims(tf.keras.utils.to_categorical(277, 1000), 0)

    st.session_state["phase2"] = True

if st.session_state["phase2"] == True:
    
    # Phase 3. Pick XAI model:
    
    option_xai = st.selectbox(
    "Choose pretrained model:",
    ('Select XAI model', 'GradCAM', 'Occlusion Sensitivity', 'Rise', 'Integrated Gradients', 'Lime', 'Shap'))
    
    if option_xai == 'Select XAI model':
        st.stop()
    
    if option_xai == 'GradCAM':
        
        st.subheader("Def.")
        st.markdown("Grad-CAM uses the gradients of any target concept (say logits for “dog” or even a caption), flowing into the final convolutional layer to produce a coarse localization map highlighting the important regions in the image for predicting the concept.")
        st.markdown("The weights of the last layer k are defined as:")
        st.latex(r'''
                 w_{k} = \frac{1}{Z} \sum_{i} \sum_{j} \frac{\partial f(x)}{\partial A^{k}_{i,j}}
                 ''')
        st.markdown("Then we aggregate features using the attribution defined as:")
        st.latex(r'''
            \theta = max(0, \sum_{k} w_{k} A^{k})
            ''')
        
        st.link_button("Go to research paper", url = "https://arxiv.org/pdf/1610.02391.pdf")
        
        explainer = GradCAMPP(model = model,
                              output_layer=-1,
                              batch_size=16,
                              conv_layer=None)

        explanation = explainer.explain(x, y)
        
        fig, axes = plt.subplots(figsize= (8,5))
        plt.sca(axes)

        axes.set_title("GradCAM")
        axes.axis("off")
        plot_attribution(explanation=explanation,
                         image= x,
                         ax = axes, 
                         cmap='cividis',
                         alpha=0.6)
        st.pyplot(fig)
    
    if option_xai == 'Occlusion Sensitivity':
        
        # Let user pick Occlusion param
        
        explainer = Occlusion(model,
                              patch_size=(12, 12), 
                              patch_stride=(4, 4),
                              batch_size=16,
                              occlusion_value=0)
        
        explanation = explainer.explain(x, y)
        
        fig, axes = plt.subplots(figsize= (8,5))
        plt.sca(axes)

        axes.set_title("Occlusion Sensitivity")
        axes.axis("off")
        plot_attribution(explanation=explanation,
                         image= x,
                         ax = axes, 
                         cmap='cividis',
                         alpha=0.6)
        st.pyplot(fig)
    
    if option_xai == 'Rise':
        
        # Let user pick Rise param
        st.markdown("Randomized Input Sampling for Explanation of Black-box Models")
        st.markdown("The Rise method is a perturbation-based method for computer vision, it generates binary masks and study the behavior of the model on masked images. The pixel influence score is the mean of all the obtained scores when the pixel was not masked.")
        st.image("download.png")
        st.link_button("Go to research paper", url="https://arxiv.org/pdf/1806.07421.pdf")
        st.link_button("Go to source code", url="https://github.com/deel-ai/xplique/blob/master/xplique/attributions/rise.py")
        nb_samples = st.number_input('Enter the sample number of masks:', step=1000)
        grid_size = st.number_input('Enter the grid size:', step=1)
        preservation_probability = st.number_input('Enter the probability of pixels to be preserved: ', step=0.1)
        explainer = Rise(model,
                         nb_samples=nb_samples,
                         grid_size=grid_size,
                         preservation_probability=preservation_probability)

        explanation = explainer.explain(x, y)

        fig, axes = plt.subplots(figsize= (8,5))
        plt.sca(axes)

        axes.set_title("Rise")
        axes.axis("off")
        plot_attribution(explanation=explanation,
                         image= x,
                         ax = axes, 
                         cmap='cividis',
                         alpha=0.6)
        st.pyplot(fig)
    
    if option_xai == 'Integrated Gradients':
        st.markdown("Integrated Gradients is a visualization technique resulting of a theoretical search for an explanatory method that satisfies two axioms, Sensitivity and Implementation Invariance (Sundararajan et al.)")
        st.link_button("Go to research paper", url="https://arxiv.org/pdf/1703.01365.pdf")
        st.link_button("Go to source code", url="https://github.com/deel-ai/xplique/blob/master/xplique/attributions/integrated_gradients.py")
        baseline_value = st.number_input('Enter the sample number of masks:', step=0.01)
        steps = st.number_input('Enter the sample number of masks:', step=10)
        explainer = IntegratedGradients(model,
                                        output_layer=-1, batch_size=16,
                                        steps=50, baseline_value=0)

        explanation = explainer.explain(x, y)

        fig, axes = plt.subplots(figsize= (8,5))
        plt.sca(axes)

        axes.set_title("Integrated Gradients")
        axes.axis("off")
        plot_attribution(explanation, x, img_size=axes, cmap='cividis', alpha=0.6)
        st.pyplot(fig)
    
    if option_xai == 'Lime':
        st.subheader("Def.")
        st.markdown(
            "The overall goal of LIME is to identify an interpretable model over the interpretable representation that is locally faithful to the classifier.")
        explainer = Lime(model = model,
                        batch_size = 16,
                        map_to_interpret_space= None,  
                        nb_samples= 4000,
                        ref_value= None, 
                        interpretable_model= linear_model.Ridge(alpha=2),
                        similarity_kernel= None, 
                        pertub_func= None,  
                        distance_mode= "euclidean",  
                        kernel_width= 45.0,  
                        prob= 0.5)
        
        explanation = explainer.explain(x, y)

        fig, axes = plt.subplots(figsize= (8,5))
        plt.sca(axes)

        axes.set_title("Lime")
        axes.axis("off")
        plot_attribution(explanation=explanation,
                         image= x,
                         ax = axes, 
                         cmap='cividis',
                         alpha=0.6)
        
        st.pyplot(fig)
    
    if option_xai == 'Shap':
        st.subheader("Def.")
        st.markdown(
            "The exact computation of SHAP values is challenging. However, by combining insights from current additive feature attribution methods, we can approximate them. We describe two model-agnostic approximation methods, [...] and another that is novel (Kernel SHAP)")
        explainer = KernelShap(model = model,
                               batch_size = 16,
                               map_to_interpret_space= None, 
                               nb_samples= 4000,
                               ref_value= None)
        
        explanation = explainer.explain(x, y)

        fig, axes = plt.subplots(figsize= (8,5))
        plt.sca(axes)

        axes.set_title("Shap")
        axes.axis("off")
        plot_attribution(explanation=explanation,
                         image= x,
                         ax = axes, 
                         cmap='cividis',
                         alpha=0.6)
        
        st.pyplot(fig) 

    st.session_state["phase3"] = True
    

    
    
    




##%%

# NEXT PHASE FOR GRADCAM

# # Method = GradCAM
# Method = GradCAMPP

# batch_size = 16
# # None will select "conv2d_93" (cf architecture)
# # Most other values will make warnings or errors
# conv_layers = [None, "conv2d_94", "conv2d_95", "conv2d_96", "conv2d_97", "conv2d_98"]

# for conv_layer in conv_layers:
#     t = time()
#     explainer = Method(model,
#                        batch_size=batch_size,
#                        conv_layer=conv_layer)

#     explanation = explainer.explain(x, y)
#     print(f"conv_layer: {conv_layer} -> {round(time()-t, 4)}s")

#     plot_attributions(explanation, x, img_size=5, cmap='cividis', alpha=0.6)
#     plt.show()


# NEXT PHASE FOR OCCLUSION

# batch_size = 16
# patch_sizes = [72, 36, 18, 9]
# # patch_stride set to a third of patch size, see next section for justifications
# occlusion_value = 0

# for patch_size in patch_sizes:
#     t = time()
#     explainer = Occlusion(model, patch_size=patch_size, patch_stride=patch_size//3,
#                           batch_size=batch_size, occlusion_value=occlusion_value)
#     explanation = explainer.explain(x, y)
#     print(f"patch_size: {patch_size} -> {round(time()-t, 4)}s")

#     plot_attributions(explanation, x, img_size=5, cmap='cividis', alpha=0.6)
#     plt.show()

# # %%