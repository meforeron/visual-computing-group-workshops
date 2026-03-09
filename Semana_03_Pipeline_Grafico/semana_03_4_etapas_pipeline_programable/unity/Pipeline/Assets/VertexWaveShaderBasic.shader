Shader "Custom/VertexWaveShader_Basic"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Amplitude ("Wave Amplitude", Float) = 0.2
        _Frequency ("Wave Frequency", Float) = 2.0
        _Speed ("Wave Speed", Float) = 2.0
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" }

        Pass
        {
            CGPROGRAM

            #pragma vertex vert
            #pragma fragment frag

            #include "UnityCG.cginc"

            sampler2D _MainTex;

            float _Amplitude;
            float _Frequency;
            float _Speed;

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float4 position : SV_POSITION;
                float2 uv : TEXCOORD0;
            };

            v2f vert (appdata v)
            {
                v2f o;

                float4 worldPos = mul(unity_ObjectToWorld, v.vertex);

                worldPos.y += sin(worldPos.x * _Frequency + _Time.y * _Speed) * _Amplitude;

                o.position = mul(UNITY_MATRIX_VP, worldPos);

                o.uv = v.uv;

                return o;
            }

            fixed4 frag (v2f i) : SV_Target
            {
                return tex2D(_MainTex, i.uv);
            }

            ENDCG
        }
    }
}