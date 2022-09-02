; waveforms.asm for MMT Blue Channel gen1
; 08aug06 last change - R. Tucker

; *** timing delays ***
P_DELAY		EQU	6000	; parallel clock delay nsecs (min 50)
S_DELAY		EQU	100	; S clock delay nsec (min 50)
DWELL		EQU	8000	; integration nsec (min 50)
PARMULT		EQU	12	; parallel delay multiplier

; *** voltages ***
RG_HI		EQU	+10.0	; Reset Gate
RG_LO		EQU	 +0.0
S_HI		EQU	 +4.0	; Serial clocks
S_LO		EQU	 -4.0
SW_HI		EQU	 +5.1	; Summing Well
SW_LO		EQU	 -4.0
P_HI		EQU	 +3.0	; Parallel clocks 
P_LO		EQU	 -6.2
TG_HI		EQU	 +3.0	; Transfer gate
TG_LO		EQU	 -6.2
VB5		EQU	  0.0	; Bias5
VB6		EQU	  0.0	; Bias6
VB7		EQU	  0.0	; Bias7

		IF CONFIG0
VOD		EQU	+26.0	; Vod
VRD		EQU	+16.0	; Vrd
VOG		EQU	  1.0	; Vog
P3_HI		EQU	+4.5
P3_LO		EQU	-4.7
VOFFSET		EQU	+0.1
		ENDIF

		IF CONFIG1
VOD		EQU	+26.0	; Vod
VRD		EQU	+16.0	; Vrd
VOG		EQU	  1.0	; Vog
P3_HI		EQU	+4.5
P3_LO		EQU	-4.7
VOFFSET		EQU	+0.1
		ENDIF

		IF CONFIG2
VOD		EQU	+26.0	; Vod
VRD		EQU	+16.0	; Vrd
VOG		EQU	  1.0	; Vog
P3_HI		EQU	 +4.5
P3_LO		EQU	 -4.7
VOFFSET		EQU	+0.1
		ENDIF

		IF CONFIG3
VOD		EQU	+26.0	; Vod
VRD		EQU	+16.0	; Vrd
VOG		EQU	  1.0	; Vog
P3_HI		EQU	+4.5
P3_LO		EQU	-4.7
VOFFSET		EQU	+0.1
		ENDIF

; *** clock rail aliases ***
S1_HI		EQU	S_HI
S1_LO		EQU	S_LO
S2_HI		EQU	S_HI
S2_LO		EQU	S_LO
S3_HI		EQU	S_HI
S3_LO		EQU	S_LO
P1_HI		EQU	P_HI
P1_LO		EQU	P_LO	
P2_HI		EQU	P_HI
P2_LO		EQU	P_LO
;P3_HI		EQU	P_HI
;P3_LO		EQU	P_LO
Q1_HI		EQU	P_HI
Q1_LO		EQU	P_LO	
Q2_HI		EQU	P_HI
Q2_LO		EQU	P_LO
Q3_HI		EQU	P3_HI
Q3_LO		EQU	P3_LO

; ITL DetChar lab in Kovar tub

; CONFIG0 - amp UL, 123t, 321w, normal mode
; CONFIG1 - amp LR, 321t, 321w, normal mode
; CONFIG2 - amp UL, 123t, 321w, mpp mode
; CONFIG3 - amp LR, 321t, 321w, mpp mode

	DEFINE	CONFIG0_PAR		'p_12_123t.asm'
	DEFINE	CONFIG0_SER		's_2_321w.asm'

	DEFINE	CONFIG1_PAR		'p_12_321t.asm'
	DEFINE	CONFIG1_SER		's_2_321w.asm'

	DEFINE	CONFIG2_PAR		'p_12_123t_mpp.asm'
	DEFINE	CONFIG2_SER		's_2_321w.asm'

	DEFINE	CONFIG3_PAR		'p_12_321t_mpp.asm'
	DEFINE	CONFIG3_SER		's_2_321w.asm'

; *** end of waveform.asm ***
